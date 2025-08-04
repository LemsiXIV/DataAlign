from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from io import StringIO
import pandas as pd
import os
from app import db
from app.models import Projet, ConfigurationCleComposee, StatistiqueEcart
from app.models.logs import LogExecution
from app.models.fichier_genere import FichierGenere
from app.services.comparateur import ComparateurFichiers
from app.services.generateur_excel import GenerateurExcel
from app.services.generateur_pdf import GenerateurPdf
from datetime import datetime, timedelta

comparaison_bp = Blueprint('comparaison', __name__)

@comparaison_bp.route('/compare', methods=['POST'])
def compare():
    keys1 = [k.strip() for k in request.form.getlist('key1')]
    keys2 = [k.strip() for k in request.form.getlist('key2')]

    try:
        df = pd.read_json(session['df_path'])
        df2 = pd.read_json(session['df2_path'])
    except Exception as e:
        flash(f"Erreur lors du chargement des fichiers JSON : {e}", "error")
        return redirect(url_for('projets.index'))

    # Nettoyer les noms de colonnes
    df.columns = df.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    # 🔍 LOGS de débogage
    print("Clés sélectionnées fichier 1 :", keys1)
    print("Clés sélectionnées fichier 2 :", keys2)
    print("Colonnes fichier 1 :", df.columns.tolist())
    print("Colonnes fichier 2 :", df2.columns.tolist())

    # Validation des clés
    if not keys1 or not keys2:
        flash("Veuillez sélectionner au moins une clé dans chaque fichier.", "error")
        return redirect(url_for('projets.index'))
        
    if not all(k in df.columns for k in keys1) or not all(k in df2.columns for k in keys2):
        flash(f"Clés invalides sélectionnées. Colonnes disponibles : {df.columns.tolist()} vs {df2.columns.tolist()}", "error")
        return redirect(url_for('projets.index'))

    # Use the comparator service
    comparateur = ComparateurFichiers(df, df2, keys1, keys2)
    results = comparateur.comparer()

    file1_name = session.get('file1_name', 'Fichier 1')
    file2_name = session.get('file2_name', 'Fichier 2')

    # Get project ID from session
    projet_id = session.get("projet_id")

    if not projet_id:
        flash("Aucun projet sélectionné. Veuillez sélectionner un projet avant de comparer.", "error")
        return redirect(url_for('projets.index'))

    # Save configurations
    config1 = ConfigurationCleComposee(
        projet_id=projet_id,
        fichier='fichier1',
        champs_concatenes=','.join(keys1)
    )
    config2 = ConfigurationCleComposee(
        projet_id=projet_id,
        fichier='fichier2',
        champs_concatenes=','.join(keys2)
    )
    db.session.add_all([config1, config2])

    # Save statistics
    stat = StatistiqueEcart(
        projet_id=projet_id,
        nb_ecarts_uniquement_fichier1=results['n1'],
        nb_ecarts_uniquement_fichier2=results['n2'],
        nb_ecarts_communs=results['n_common'],
        date_execution=datetime.now()
    )
    db.session.add(stat)

    db.session.commit()

    # Auto-generate Excel and PDF files and save them to archive
    project_folder = session.get('project_folder')
    
    # If project_folder not in session, get it from database
    if not project_folder and projet_id:
        projet = Projet.query.get(projet_id)
        if projet and projet.emplacement_archive:
            project_folder = projet.emplacement_archive
    
    if project_folder and os.path.exists(project_folder):
        try:
            # Generate Excel file
            generateur_excel = GenerateurExcel(
                results['ecarts_fichier1'], 
                results['ecarts_fichier2'], 
                results['communs'],
                project_folder
            )
            
            # Save Excel file to project archive folder
            excel_filename = f"rapport_comparaison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            excel_path = os.path.join(project_folder, excel_filename)
            generateur_excel.generer_rapport_fichier(excel_path)
            
            # Generate PDF file
            generateur_pdf = GenerateurPdf(
                results['ecarts_fichier1'],
                results['ecarts_fichier2'],
                file1_name,
                file2_name,
                len(df),
                len(df2),
                results['n_common'],
                project_folder
            )
            
            # Save PDF file to project archive folder
            pdf_filename = f"rapport_comparaison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(project_folder, pdf_filename)
            generateur_pdf.generer_pdf_fichier(pdf_path)
            
            # Log success for file generation
            log = LogExecution(
                projet_id=projet_id,
                statut='succès',
                message=f"Rapports Excel et PDF générés automatiquement - {results['n_common']} enregistrements communs, {len(results['ecarts_fichier1'])} écarts fichier 1, {len(results['ecarts_fichier2'])} écarts fichier 2"
            )
            db.session.add(log)
            
            # Save generated files info to database
            projet = Projet.query.get(projet_id)
            if projet:
                # Check if there's already a recent treatment (within 5 minutes) for this project
                cutoff_time = datetime.now() - timedelta(minutes=5)
                
                fichier_existant = FichierGenere.query.filter(
                    FichierGenere.projet_id == projet_id,
                    FichierGenere.date_execution >= cutoff_time
                ).order_by(FichierGenere.date_execution.desc()).first()
                
                if fichier_existant:
                    # Update existing record with new files
                    fichier_existant.nom_fichier_excel = excel_filename
                    fichier_existant.nom_fichier_pdf = pdf_filename
                    fichier_existant.nom_fichier_graphe = "pie_chart.png"
                    fichier_existant.date_execution = datetime.now()
                else:
                    # Create new treatment record
                    nom_traitement = f"Traitement_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    fichier_genere = FichierGenere(
                        projet_id=projet_id,
                        nom_traitement_projet=nom_traitement,
                        nom_fichier_excel=excel_filename,
                        nom_fichier_pdf=pdf_filename,
                        nom_fichier_graphe="pie_chart.png",
                        chemin_archive=projet.emplacement_archive,
                        date_execution=datetime.now()
                    )
                    db.session.add(fichier_genere)
            
            db.session.commit()
            
            # Add flash message to inform user that files were auto-generated
            flash(f"Rapport de comparaison terminé ! Les fichiers Excel et PDF ont été automatiquement sauvegardés dans le dossier d'archive du projet.", "success")
            
        except Exception as e:
            # Log failure for file generation
            log = LogExecution(
                projet_id=projet_id,
                statut='échec',
                message=f"Échec génération automatique des rapports: {str(e)}"
            )
            db.session.add(log)
            db.session.commit()
            
            # Don't fail the comparison, just log the error
            print(f"Erreur lors de la génération automatique des fichiers: {e}")
    else:
        # Log when project folder is not available
        log = LogExecution(
            projet_id=projet_id,
            statut='échec',
            message=f"Impossible de générer les rapports automatiquement: dossier projet non trouvé"
        )
        db.session.add(log)
        db.session.commit()
        
        # Add flash message to inform user
        flash("Comparaison terminée, mais les rapports n'ont pas pu être sauvegardés automatiquement. Utilisez les boutons de téléchargement pour obtenir les fichiers.", "warning")

    return render_template("compare.html",
                           key1=' + '.join(keys1),
                           key2=' + '.join(keys2),
                           ecarts1=results['ecarts_fichier1'].to_dict(orient='records'),
                           ecarts2=results['ecarts_fichier2'].to_dict(orient='records'),
                           file1_name=file1_name,
                           file2_name=file2_name,
                           **results)

@comparaison_bp.route('/Fast_Compare', methods=['POST'])
def fast_compare():
    try:
        df = pd.read_json(session['df_path'])
        df2 = pd.read_json(session['df2_path'])
    except Exception as e:
        flash(f"Erreur lors de la lecture des fichiers JSON : {e}", "error")
        return redirect(url_for('projets.index'))

    keys1 = [k.strip() for k in request.form.getlist('key1')]
    keys2 = [k.strip() for k in request.form.getlist('key2')]

    # Nettoyer colonnes
    df.columns = df.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    if not keys1 or not keys2:
        flash("Veuillez sélectionner au moins une clé dans chaque fichier.", "error")
        return redirect(url_for('projets.index'))

    if not all(k in df.columns for k in keys1) or not all(k in df2.columns for k in keys2):
        flash("Clés invalides sélectionnées.", "error")
        return redirect(url_for('projets.index'))

    # Appeler ton comparateur personnalisé
    comparateur = ComparateurFichiers(df, df2, keys1, keys2)
    results = comparateur.comparer()

    return render_template("compare.html",
                           key1=' + '.join(keys1),
                           key2=' + '.join(keys2),
                           ecarts1=results['ecarts_fichier1'].to_dict(orient='records'),
                           ecarts2=results['ecarts_fichier2'].to_dict(orient='records'),
                           file1_name=session.get('file1_name', 'Fichier 1'),
                           file2_name=session.get('file2_name', 'Fichier 2'),
                           **results)
