from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from io import StringIO
import pandas as pd
import os
import uuid
from datetime import datetime
from app import db
from app.models import Projet
from app.models.logs import LogExecution
from app.services.lecteur_fichier import read_uploaded_file
from app.services.generateur_excel import GenerateurExcel
from app.services.generateur_pdf import GenerateurPdf
from app.services.comparateur import ComparateurFichiers

fichiers_bp = Blueprint('fichiers', __name__)

@fichiers_bp.route('/upload', methods=['POST'])
def upload_file():
    session.clear() # Clear session to avoid conflicts with previous uploads
    if 'file' not in request.files or 'file2' not in request.files:
        flash("Veuillez sélectionner les deux fichiers", "error")
        return redirect(url_for('projets.index'))

    file = request.files['file']
    file2 = request.files['file2']

    if file.filename == '' or file2.filename == '':
        flash("Un des fichiers est vide", "error")
        return redirect(url_for('projets.index'))

    # Get form values
    nom_projet = request.form.get('name')
    projet_existant_id = request.form.get('existing_project')
    

    try:
        date_execution = datetime.now().date()
    except Exception as e:
        flash(f"Date invalide : {e}", "error")
        return redirect(url_for('projets.index'))

    # Save files to archive directory with renamed format
    archive_folder = os.path.join('uploads', 'archive')
    os.makedirs(archive_folder, exist_ok=True)  # Create archive folder if it doesn't exist
    
    # Generate datetime string for file naming
    datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Project logic
    if projet_existant_id:
        projet = Projet.query.get(int(projet_existant_id))
        if not projet:
            flash("Projet sélectionné introuvable", "error")
            return redirect(url_for('projets.index'))
        actual_project_name = projet.nom_projet
        
        # Ajouter une trace dans logs_execution pour l'utilisation d'un projet existant
        log = LogExecution(
            projet_id=projet.id,
            statut='succès',
            message=f"Fichiers ajoutés au projet existant: {actual_project_name} - {file.filename} et {file2.filename}"
        )
        db.session.add(log)
        db.session.commit()
    else:
        if not nom_projet:
            flash("Veuillez saisir un nom de projet ou en sélectionner un existant.", "error")
            return redirect(url_for('projets.index'))
        actual_project_name = nom_projet

        projet = Projet(
            nom_projet=nom_projet,
            date_creation=date_execution,
            fichier_1="",  # Will be updated after file saving
            fichier_2="",  # Will be updated after file saving
            emplacement_source="",  # Will be updated after directory creation
            emplacement_archive=""  # Will be updated after directory creation
        )
        db.session.add(projet)
        db.session.commit()
        
        # Ajouter une trace dans logs_execution pour la création du projet
        log = LogExecution(
            projet_id=projet.id,
            statut='succès',
            message=f"Nouveau projet créé: {nom_projet} avec fichiers {file.filename} et {file2.filename}"
        )
        db.session.add(log)
        db.session.commit()

    # Create project-specific directory within archive using actual project name
    project_dir_name = f"{actual_project_name}_{datetime_str}"
    project_folder = os.path.join(archive_folder, project_dir_name)
    os.makedirs(project_folder, exist_ok=True)
    
    # Create new filenames with format: original_name_datetime_original.extension
    file1_name, file1_ext = os.path.splitext(file.filename)
    file2_name, file2_ext = os.path.splitext(file2.filename)
    
    new_file1_name = f"{file1_name}_{datetime_str}_original{file1_ext}"
    new_file2_name = f"{file2_name}_{datetime_str}_original{file2_ext}"
    
    filepath = os.path.join(project_folder, new_file1_name)
    filepath2 = os.path.join(project_folder, new_file2_name)
    file.save(filepath)
    file2.save(filepath2)

    # Update project with file and folder information if it's a new project
    if not projet_existant_id:
        projet.fichier_1 = new_file1_name
        projet.fichier_2 = new_file2_name
        projet.emplacement_source = project_folder
        projet.emplacement_archive = project_folder
        db.session.commit()

    # Read the saved files into DataFrames
    try:
        df = pd.read_csv(filepath) if file.filename.endswith('.csv') else (
             pd.read_excel(filepath) if file.filename.endswith(('.xls', '.xlsx')) else pd.read_json(filepath))
        df2 = pd.read_csv(filepath2) if file2.filename.endswith('.csv') else (
              pd.read_excel(filepath2) if file2.filename.endswith(('.xls', '.xlsx')) else pd.read_json(filepath2))
        print("Colonnes fichier 1 après lecture :", df.columns.tolist())
        print("Colonnes fichier 2 après lecture :", df2.columns.tolist())
    except Exception as e:
        # Ajouter une trace d'échec dans logs_execution
        log = LogExecution(
            projet_id=projet.id,
            statut='échec',
            message=f"Erreur lors de la lecture des fichiers pour le projet {actual_project_name}: {str(e)}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f"Erreur de lecture : {e}", "error")
        return redirect(url_for('projets.index'))

    # Chemin du dossier temporaire
    temp_folder = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_folder, exist_ok=True)  # ✅ Crée le dossier s'il n'existe pas


    # Sauvegarde des dataframes dans des fichiers temporaires
    df_id = str(uuid.uuid4())
    df2_id = str(uuid.uuid4())
    df_path = os.path.join("temp", f"{df_id}.json")
    df2_path = os.path.join("temp", f"{df2_id}.json")

    df.to_json(df_path, orient="records", force_ascii=False)
    df2.to_json(df2_path, orient="records", force_ascii=False)

    # Stocker uniquement les chemins
    session['projet_id'] = projet.id
    session['df_path'] = df_path
    session['df2_path'] = df2_path
    session['file1_name'] = file.filename
    session['file2_name'] = file2.filename
    session['project_folder'] = project_folder  # Store project folder for Excel/PDF generation

    # Ajouter une trace de succès final pour le traitement des fichiers
    log = LogExecution(
        projet_id=projet.id,
        statut='succès',
        message=f"Fichiers traités avec succès pour le projet {actual_project_name} - {len(df)} lignes dans {file.filename}, {len(df2)} lignes dans {file2.filename}"
    )
    db.session.add(log)
    db.session.commit()

    return render_template('index.html',
                           data=df.to_dict(orient='records'),
                           columns=df.columns.tolist(),
                           data2=df2.to_dict(orient='records'),
                           columns2=df2.columns.tolist(),
                           form_action=url_for('comparaison.compare'))

@fichiers_bp.route('/fast_test', methods=['POST'])
def fast_upload():
    session.clear()  # Nettoyer la session

    if 'file_fast_upload' not in request.files or 'file_fast_upload2' not in request.files:
        flash("Veuillez sélectionner les deux fichiers", "error")
        return redirect(url_for('projets.index'))

    file = request.files['file_fast_upload']
    file2 = request.files['file_fast_upload2']

    if file.filename == '' or file2.filename == '':
        flash("Un des fichiers est vide", "error")
        return redirect(url_for('projets.index'))

    try:
        df = read_uploaded_file(file)
        df2 = read_uploaded_file(file2)
    except Exception as e:
        # Ajouter une trace d'échec pour le test rapide
        log = LogExecution(
            projet_id=None,  # Pas de projet pour les tests rapides
            statut='échec',
            message=f"Erreur lors du test rapide avec fichiers {file.filename} et {file2.filename}: {str(e)}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f"Erreur lors de la lecture des fichiers : {e}", "error")
        return redirect(url_for('projets.index'))

    # ✅ Créer le dossier temp si non existant
    temp_folder = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_folder, exist_ok=True)

    # ✅ Sauvegarder les DataFrame dans des fichiers temporaires
    df_id = str(uuid.uuid4())
    df2_id = str(uuid.uuid4())
    df_path = os.path.join(temp_folder, f"{df_id}.json")
    df2_path = os.path.join(temp_folder, f"{df2_id}.json")

    df.to_json(df_path, orient="records", force_ascii=False)
    df2.to_json(df2_path, orient="records", force_ascii=False)

    # ✅ Sauvegarder les chemins dans la session (léger)
    session['df_path'] = df_path
    session['df2_path'] = df2_path
    session['file1_name'] = file.filename
    session['file2_name'] = file2.filename

    # Ajouter une trace de succès pour le test rapide
    log = LogExecution(
        projet_id=None,  # Pas de projet pour les tests rapides
        statut='succès',
        message=f"Test rapide réussi avec fichiers {file.filename} et {file2.filename} - {len(df)} et {len(df2)} lignes"
    )
    db.session.add(log)
    db.session.commit()

    return render_template('index.html', 
                            data=df.to_dict(orient='records'), 
                            columns=df.columns.tolist(), 
                            data2=df2.to_dict(orient='records'), 
                            columns2=df2.columns.tolist(),
                            form_action=url_for('comparaison.fast_compare'))

@fichiers_bp.route('/download')
def download_excel():
    projet_id = session.get('projet_id')
    try:
        # Load data from saved JSON files instead of session
        df_path = session.get('df_path')
        df2_path = session.get('df2_path')
        
        if not df_path or not df2_path:
            # Log d'échec pour données manquantes
            log = LogExecution(
                projet_id=projet_id,
                statut='échec',
                message="Échec génération Excel: Données non trouvées dans la session"
            )
            db.session.add(log)
            db.session.commit()
            
            flash("Données non trouvées dans la session", "error")
            return redirect(url_for('projets.index'))
            
        df = pd.read_json(df_path)
        df2 = pd.read_json(df2_path)
    except Exception as e:
        # Log d'échec pour erreur de chargement
        log = LogExecution(
            projet_id=projet_id,
            statut='échec',
            message=f"Échec génération Excel: Erreur lors du chargement des données - {str(e)}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f"Erreur lors du chargement des données pour export : {e}", "error")
        return redirect(url_for('projets.index'))

    keys1 = request.args.getlist('key1')
    keys2 = request.args.getlist('key2')

    if not keys1 or not keys2:
        # Log d'échec pour clés manquantes
        log = LogExecution(
            projet_id=projet_id,
            statut='échec',
            message="Échec génération Excel: Clés de comparaison manquantes"
        )
        db.session.add(log)
        db.session.commit()
        
        flash("Clés manquantes pour la génération du fichier", "error")
        return redirect(url_for('projets.index'))

    # Use comparator to get results
    comparateur = ComparateurFichiers(df, df2, keys1, keys2)
    results = comparateur.comparer()

    # Generate Excel
    generateur = GenerateurExcel(
        results['ecarts_fichier1'], 
        results['ecarts_fichier2'], 
        results['communs'],
        session.get('project_folder')  # Pass project folder for saving
    )
    
    # Log de succès pour la génération Excel
    log = LogExecution(
        projet_id=projet_id,
        statut='succès',
        message=f"Rapport Excel généré avec succès - {results['n_common']} enregistrements communs, {len(results['ecarts_fichier1'])} écarts fichier 1, {len(results['ecarts_fichier2'])} écarts fichier 2"
    )
    db.session.add(log)
    db.session.commit()
    
    return generateur.generer_rapport()

@fichiers_bp.route('/download_pdf')
def download_pdf():
    projet_id = session.get('projet_id')
    try:
        # Load data from saved JSON files instead of session
        df_path = session.get('df_path')
        df2_path = session.get('df2_path')
        
        if not df_path or not df2_path:
            # Log d'échec pour données manquantes
            log = LogExecution(
                projet_id=projet_id,
                statut='échec',
                message="Échec génération PDF: Données non trouvées dans la session"
            )
            db.session.add(log)
            db.session.commit()
            
            flash("Données non trouvées dans la session", "error")
            return redirect(url_for('projets.index'))
            
        df = pd.read_json(df_path)
        df2 = pd.read_json(df2_path)
    except Exception as e:
        # Log d'échec pour erreur de chargement
        log = LogExecution(
            projet_id=projet_id,
            statut='échec',
            message=f"Échec génération PDF: Erreur lors du chargement des données - {str(e)}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f"Erreur : {e}", "error")
        return redirect(url_for('projets.index'))

    keys1 = request.args.getlist('key1')
    keys2 = request.args.getlist('key2')

    # Use comparator to get results
    comparateur = ComparateurFichiers(df, df2, keys1, keys2)
    results = comparateur.comparer()

    # Generate PDF
    generateur = GenerateurPdf(
        results['ecarts_fichier1'],
        results['ecarts_fichier2'],
        session.get('file1_name'),
        session.get('file2_name'),
        len(df),
        len(df2),
        results['n_common'],
        session.get('project_folder')  # Pass project folder for saving
    )
    
    try:
        # Log de succès pour la génération PDF
        log = LogExecution(
            projet_id=projet_id,
            statut='succès',
            message=f"Rapport PDF généré avec succès - {results['n_common']} enregistrements communs, {len(results['ecarts_fichier1'])} écarts fichier 1, {len(results['ecarts_fichier2'])} écarts fichier 2"
        )
        db.session.add(log)
        db.session.commit()
        
        return generateur.generer_pdf()
    except Exception as e:
        # Log d'échec pour erreur de génération PDF
        log = LogExecution(
            projet_id=projet_id,
            statut='échec',
            message=f"Échec génération PDF: Erreur lors de la génération - {str(e)}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f"Erreur lors de la génération du PDF : {e}", "error")
        return redirect(url_for('projets.index'))
