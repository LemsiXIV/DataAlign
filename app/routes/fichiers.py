from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_file
from io import StringIO
import pandas as pd
import os
import uuid
from datetime import datetime
from app import db
from app.models import Projet
from app.models.logs import LogExecution
from app.models.fichier_genere import FichierGenere
from app.services.lecteur_fichier import read_uploaded_file
from app.services.lecteur_fichier_optimise import read_uploaded_file_optimized, LecteurFichierOptimise
from app.services.generateur_excel import GenerateurExcel
from app.services.generateur_pdf import GenerateurPdf
from app.services.comparateur import ComparateurFichiers
from app.services.comparateur_optimise import ComparateurFichiersOptimise, compare_large_files

fichiers_bp = Blueprint('fichiers', __name__)

def render_index_with_errors(file1_error=None, file2_error=None, project_error=None, show_fast_modal=False, show_main_modal=False):
    """Helper function to render index with specific field errors"""
    projets = Projet.query.all()
    return render_template('index.html', 
                         projets=projets,
                         file1_error=file1_error,
                         file2_error=file2_error, 
                         project_error=project_error,
                         show_fast_modal=show_fast_modal,
                         show_main_modal=show_main_modal)

@fichiers_bp.route('/upload', methods=['POST'])
def upload_file():
    session.clear() # Clear session to avoid conflicts with previous uploads
    if 'file' not in request.files or 'file2' not in request.files:
        return render_index_with_errors(project_error="Veuillez sélectionner les deux fichiers", show_main_modal=True)

    file = request.files['file']
    file2 = request.files['file2']

    if file.filename == '':
        return render_index_with_errors(file1_error="Aucun fichier sélectionné", show_main_modal=True)
    if file2.filename == '':
        return render_index_with_errors(file2_error="Vous n'avez pas sélectionné le 2ème fichier", show_main_modal=True)

    # Get form values
    nom_projet = request.form.get('name')
    projet_existant_id = request.form.get('existing_project')

    try:
        date_execution = datetime.now()
    except Exception as e:
        return render_index_with_errors(project_error=f"Date invalide : {e}", show_main_modal=True)

    # Save files to archive directory with renamed format
    archive_folder = os.path.join('uploads', 'archive')
    os.makedirs(archive_folder, exist_ok=True)
    
    # Generate datetime string for file naming
    datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Project logic
    if projet_existant_id:
        projet = Projet.query.get(int(projet_existant_id))
        if not projet:
            return render_index_with_errors(project_error="Projet sélectionné introuvable", show_main_modal=True)
        actual_project_name = projet.nom_projet
        
        # Log for existing project
        log = LogExecution(
            projet_id=projet.id,
            statut='succès',
            message=f"Fichiers ajoutés au projet existant: {actual_project_name} - {file.filename} et {file2.filename}"
        )
        db.session.add(log)
        db.session.commit()
    else:
        if not nom_projet:
            return render_index_with_errors(project_error="Veuillez saisir un nom de projet ou en sélectionner un existant.", show_main_modal=True)
        actual_project_name = nom_projet

        projet = Projet(
            nom_projet=nom_projet,
            date_creation=date_execution,
            fichier_1=file.filename,
            fichier_2=file2.filename,
            emplacement_source="",
            emplacement_archive=""
        )
        db.session.add(projet)
        db.session.commit()
        
        # Log for new project
        log = LogExecution(
            projet_id=projet.id,
            statut='succès',
            message=f"Nouveau projet créé: {nom_projet} avec fichiers {file.filename} et {file2.filename}"
        )
        db.session.add(log)
        db.session.commit()

    # Create project directory
    project_dir_name = f"{actual_project_name}_{datetime_str}"
    project_folder = os.path.join(archive_folder, project_dir_name)
    os.makedirs(project_folder, exist_ok=True)
    
    # Create new filenames
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
    else:
        # For existing projects, update the folder paths if they're empty
        if not projet.emplacement_source or not projet.emplacement_archive:
            projet.emplacement_source = project_folder
            projet.emplacement_archive = project_folder
            db.session.commit()

    # Read files using optimized approach
    try:
        lecteur = LecteurFichierOptimise()
        
        # Get file info to determine if files are large
        file1_info = lecteur.read_file_info(filepath)
        file2_info = lecteur.read_file_info(filepath2)
        
        # Determine if files are large (over 5k rows or 50 columns)
        is_large_file1 = file1_info['total_rows'] > 5000 or file1_info['total_columns'] > 50
        is_large_file2 = file2_info['total_rows'] > 5000 or file2_info['total_columns'] > 50
        
        print(f"File 1 info: {file1_info['total_rows']} rows, {file1_info['total_columns']} columns")
        print(f"File 2 info: {file2_info['total_rows']} rows, {file2_info['total_columns']} columns")
        
        if is_large_file1 or is_large_file2:
            # For large files, get small samples for preview only
            print("Large files detected - using optimized processing")
            df = lecteur.get_file_sample(filepath, 100)  # Very small sample
            df2 = lecteur.get_file_sample(filepath2, 100)  # Very small sample
            
            # Store minimal info in session
            session['is_large_files'] = True
            session['file1_info'] = {
                'total_rows': file1_info['total_rows'],
                'total_columns': file1_info['total_columns']
            }
            session['file2_info'] = {
                'total_rows': file2_info['total_rows'], 
                'total_columns': file2_info['total_columns']
            }
            session['file1_path'] = filepath
            session['file2_path'] = filepath2
            
            print(f"Using samples: {len(df)} and {len(df2)} rows for preview")
            
        else:
            # For smaller files, read normally
            df = pd.read_csv(filepath) if file.filename.endswith('.csv') else (
                 pd.read_excel(filepath) if file.filename.endswith(('.xls', '.xlsx')) else pd.read_json(filepath))
            df2 = pd.read_csv(filepath2) if file2.filename.endswith('.csv') else (
                  pd.read_excel(filepath2) if file2.filename.endswith(('.xls', '.xlsx')) else pd.read_json(filepath2))
            session['is_large_files'] = False
            
            # Store in temporary files only for small files
            temp_folder = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_folder, exist_ok=True)
            
            df_id = str(uuid.uuid4())
            df2_id = str(uuid.uuid4())
            df_path = os.path.join("temp", f"{df_id}.json")
            df2_path = os.path.join("temp", f"{df2_id}.json")

            df.to_json(df_path, orient="records", force_ascii=False)
            df2.to_json(df2_path, orient="records", force_ascii=False)
            
            session['df_path'] = df_path
            session['df2_path'] = df2_path
        
        print("Colonnes fichier 1 après lecture :", df.columns.tolist()[:10])  # Only show first 10
        print("Colonnes fichier 2 après lecture :", df2.columns.tolist()[:10])  # Only show first 10
        
        # Check if files are empty
        file1_empty = df.empty or len(df) == 0 or df.shape[0] == 0
        file2_empty = df2.empty or len(df2) == 0 or df2.shape[0] == 0
        
        if file1_empty and file2_empty:
            log = LogExecution(
                projet_id=projet.id,
                statut='échec',
                message=f"Les deux fichiers sont vides pour le projet {actual_project_name}"
            )
            db.session.add(log)
            db.session.commit()
            return render_index_with_errors(file1_error="Le fichier est vide", file2_error="Le fichier est vide", show_main_modal=True)
        elif file1_empty:
            log = LogExecution(
                projet_id=projet.id,
                statut='échec',
                message=f"Le premier fichier est vide pour le projet {actual_project_name}"
            )
            db.session.add(log)
            db.session.commit()
            return render_index_with_errors(file1_error="Le premier fichier est vide", show_main_modal=True)
        elif file2_empty:
            log = LogExecution(
                projet_id=projet.id,
                statut='échec',
                message=f"Le deuxième fichier est vide pour le projet {actual_project_name}"
            )
            db.session.add(log)
            db.session.commit()
            return render_index_with_errors(file2_error="Le deuxième fichier est vide", show_main_modal=True)
            
    except Exception as e:
        log = LogExecution(
            projet_id=projet.id,
            statut='échec',
            message=f"Erreur lors de la lecture des fichiers pour le projet {actual_project_name}: {str(e)}"
        )
        db.session.add(log)
        db.session.commit()
        return render_index_with_errors(project_error=f"Erreur de lecture : {e}", show_main_modal=True)

    # Store session data
    session['projet_id'] = projet.id
    session['file1_name'] = file.filename
    session['file2_name'] = file2.filename
    session['project_folder'] = project_folder

    # Log success
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
                           form_action=url_for('comparaison.compare'),
                           is_large_files=session.get('is_large_files', False),
                           file1_info=session.get('file1_info'),
                           file2_info=session.get('file2_info'))

@fichiers_bp.route('/fast_test', methods=['POST'])
def fast_upload():
    session.clear()

    if 'file_fast_upload' not in request.files or 'file_fast_upload2' not in request.files:
        return render_index_with_errors(project_error="Veuillez sélectionner les deux fichiers", show_fast_modal=True)

    file = request.files['file_fast_upload']
    file2 = request.files['file_fast_upload2']

    if file.filename == '':
        return render_index_with_errors(file1_error="Vous n'avez pas sélectionné le 1er fichier", show_fast_modal=True)
    if file2.filename == '':
        return render_index_with_errors(file2_error="Vous n'avez pas sélectionné le 2ème fichier", show_fast_modal=True)

    try:
        # Use optimized file reader for fast tests
        result1 = read_uploaded_file_optimized(file, max_preview_rows=100)  # Smaller preview
        result2 = read_uploaded_file_optimized(file2, max_preview_rows=100)  # Smaller preview
        
        df = result1['data']
        df2 = result2['data']
        
        # Store file information in session
        session['is_large_files'] = result1['is_large_file'] or result2['is_large_file']
        if result1['is_large_file']:
            session['file1_path'] = result1['temp_path']
            session['file1_info'] = {
                'total_rows': result1['file_info']['total_rows'],
                'total_columns': result1['file_info']['total_columns']
            }
        if result2['is_large_file']:
            session['file2_path'] = result2['temp_path']
            session['file2_info'] = {
                'total_rows': result2['file_info']['total_rows'],
                'total_columns': result2['file_info']['total_columns']
            }
        
        # Check if files are empty
        file1_empty = df.empty or len(df) == 0 or df.shape[0] == 0
        file2_empty = df2.empty or len(df2) == 0 or df2.shape[0] == 0
        
        if file1_empty and file2_empty:
            return render_index_with_errors(file1_error="Le fichier est vide", file2_error="Le fichier est vide", show_fast_modal=True)
        elif file1_empty:
            return render_index_with_errors(file1_error="Le premier fichier est vide", show_fast_modal=True)
        elif file2_empty:
            return render_index_with_errors(file2_error="Le deuxième fichier est vide", show_fast_modal=True)
            
    except Exception as e:
        return render_index_with_errors(project_error=f"Erreur lors de la lecture des fichiers : {e}", show_fast_modal=True)

    # Create temp files for small files only
    if not session.get('is_large_files', False):
        temp_folder = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_folder, exist_ok=True)

        df_id = str(uuid.uuid4())
        df2_id = str(uuid.uuid4())
        df_path = os.path.join(temp_folder, f"{df_id}.json")
        df2_path = os.path.join(temp_folder, f"{df2_id}.json")

        df.to_json(df_path, orient="records", force_ascii=False)
        df2.to_json(df2_path, orient="records", force_ascii=False)

        session['df_path'] = df_path
        session['df2_path'] = df2_path

    session['file1_name'] = file.filename
    session['file2_name'] = file2.filename

    return render_template('index.html', 
                            data=df.to_dict(orient='records'), 
                            columns=df.columns.tolist(), 
                            data2=df2.to_dict(orient='records'), 
                            columns2=df2.columns.tolist(),
                            form_action=url_for('comparaison.fast_compare'),
                            is_large_files=session.get('is_large_files', False),
                            file1_info=session.get('file1_info'),
                            file2_info=session.get('file2_info'))

# Debug route (remove in production)
@fichiers_bp.route('/debug_session')
def debug_session():
    return f"Session data: {dict(session)}"

@fichiers_bp.route('/download_excel')
def download_excel():
    """Download comparison results as Excel file"""
    try:
        from ..services.generateur_excel import generer_excel
        
        # Check if we have comparison results path in session
        if 'download_results_path' not in session:
            flash('Aucun résultat de comparaison disponible pour le téléchargement.', 'error')
            return redirect(url_for('fichiers.upload_file'))
        
        # Load DataFrames from temporary file
        import pickle
        import os
        
        temp_path = session['download_results_path']
        if not os.path.exists(temp_path):
            flash('Les résultats de comparaison ont expiré. Veuillez refaire la comparaison.', 'error')
            return redirect(url_for('fichiers.upload_file'))
        
        with open(temp_path, 'rb') as f:
            resultats = pickle.load(f)
        
        # Generate Excel file
        excel_path = generer_excel(resultats)
        
        if excel_path and os.path.exists(excel_path):
            return send_file(excel_path, as_attachment=True, 
                           download_name=f"comparaison_resultats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        else:
            flash('Erreur lors de la génération du fichier Excel.', 'error')
            return redirect(url_for('fichiers.upload_file'))
            
    except Exception as e:
        flash(f'Erreur lors du téléchargement: {str(e)}', 'error')
        return redirect(url_for('fichiers.upload_file'))

@fichiers_bp.route('/download_pdf')
def download_pdf():
    """Download comparison results as PDF file"""
    try:
        from ..services.generateur_pdf import generer_pdf
        
        # Check if we have comparison results path in session
        if 'download_results_path' not in session:
            flash('Aucun résultat de comparaison disponible pour le téléchargement.', 'error')
            return redirect(url_for('fichiers.upload_file'))
        
        # Load DataFrames from temporary file
        import pickle
        import os
        
        temp_path = session['download_results_path']
        if not os.path.exists(temp_path):
            flash('Les résultats de comparaison ont expiré. Veuillez refaire la comparaison.', 'error')
            return redirect(url_for('fichiers.upload_file'))
        
        with open(temp_path, 'rb') as f:
            resultats = pickle.load(f)
        
        # Generate PDF file
        pdf_path = generer_pdf(resultats)
        
        if pdf_path and os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True,
                           download_name=f"comparaison_resultats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        else:
            flash('Erreur lors de la génération du fichier PDF.', 'error')
            return redirect(url_for('fichiers.upload_file'))
            
    except Exception as e:
        flash(f'Erreur lors du téléchargement: {str(e)}', 'error')
        return redirect(url_for('fichiers.upload_file'))
