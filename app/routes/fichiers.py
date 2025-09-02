from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_file
from flask_login import current_user
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
    # Clear only file-related session data to avoid conflicts with previous uploads
    file_session_keys = ['df_path', 'df2_path', 'file1_path', 'file2_path', 'file1_info', 'file2_info', 
                        'is_large_files', 'projet_id', 'file1_name', 'file2_name', 'project_folder',
                        'download_results_path']
    for key in file_session_keys:
        session.pop(key, None)
    
    # Ensure user is logged in for project creation
    if not current_user.is_authenticated:
        flash('Vous devez être connecté pour créer ou modifier un projet.', 'error')
        return redirect(url_for('auth.login'))
    
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
            fichier_1="",  # Will be updated after file processing
            fichier_2="",  # Will be updated after file processing
            emplacement_source="",
            emplacement_archive="",
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(projet)
        db.session.commit()
        
        # Log for new project
        log = LogExecution(
            projet_id=projet.id,
            statut='succès',
            message=f"Nouveau projet créé: {nom_projet} par utilisateur {current_user.username if current_user.is_authenticated else 'Anonyme'}"
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

    # Update project with file and folder information
    if not projet_existant_id:
        # For new projects, update with the renamed filenames and folder paths
        projet.fichier_1 = new_file1_name
        projet.fichier_2 = new_file2_name
        projet.emplacement_source = project_folder
        projet.emplacement_archive = project_folder
        db.session.commit()
        
        # Update log with file information
        log = LogExecution(
            projet_id=projet.id,
            statut='succès',
            message=f"Fichiers sauvegardés pour le projet {actual_project_name}: {new_file1_name} et {new_file2_name} dans {project_folder}"
        )
        db.session.add(log)
        db.session.commit()
    else:
        # For existing projects, update the folder paths if they're empty
        if not projet.emplacement_source or not projet.emplacement_archive:
            projet.emplacement_source = project_folder
            projet.emplacement_archive = project_folder
            db.session.commit()
        
        # Log for existing project file addition
        log = LogExecution(
            projet_id=projet.id,
            statut='succès',
            message=f"Nouveaux fichiers ajoutés au projet {actual_project_name}: {new_file1_name} et {new_file2_name} dans {project_folder}"
        )
        db.session.add(log)
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
            # For smaller files, read normally with encoding detection
            def safe_read_csv_local(filepath, filename):
                """Safely read CSV with multiple encoding attempts and error handling"""
                from app.utils.encoding_utils import safe_read_csv
                try:
                    return safe_read_csv(filepath)
                except Exception as e:
                    raise ValueError(f"Erreur lors de la lecture du fichier {filename}: {str(e)}")
            
            if file.filename.endswith('.csv'):
                df = safe_read_csv_local(filepath, file.filename)
            elif file.filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(filepath)
            else:
                df = pd.read_json(filepath)
                
            if file2.filename.endswith('.csv'):
                df2 = safe_read_csv_local(filepath2, file2.filename)
            elif file2.filename.endswith(('.xls', '.xlsx')):
                df2 = pd.read_excel(filepath2)
            else:
                df2 = pd.read_json(filepath2)
                
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
    # Clear only file-related session data
    file_session_keys = ['df_path', 'df2_path', 'file1_path', 'file2_path', 'file1_info', 'file2_info', 
                        'is_large_files', 'projet_id', 'file1_name', 'file2_name', 'project_folder',
                        'download_results_path']
    for key in file_session_keys:
        session.pop(key, None)

    if 'file_fast_upload' not in request.files or 'file_fast_upload2' not in request.files:
        return render_index_with_errors(project_error="Veuillez sélectionner les deux fichiers", show_fast_modal=True)

    file = request.files['file_fast_upload']
    file2 = request.files['file_fast_upload2']

    if file.filename == '':
        return render_index_with_errors(file1_error="Vous n'avez pas sélectionné le 1er fichier", show_fast_modal=True)
    if file2.filename == '':
        return render_index_with_errors(file2_error="Vous n'avez pas sélectionné le 2ème fichier", show_fast_modal=True)

    try:
        # Check if GPT processing is enabled
        enable_gpt = request.form.get('enable_gpt') == 'true'
        
        # Use optimized file reader for fast tests
        result1 = read_uploaded_file_optimized(file, max_preview_rows=100)  # Smaller preview
        result2 = read_uploaded_file_optimized(file2, max_preview_rows=100)  # Smaller preview
        
        df = result1['data']
        df2 = result2['data']
        
        # Apply GPT processing if enabled
        if enable_gpt:
            try:
                from ..services.gpt_data_processor import GPTDataProcessor
                from ..config import Config
                import os
                
                # Debug: Print the actual config values
                print(f"🔍 Debug - Config.ENABLE_GPT_PROCESSING: {Config.ENABLE_GPT_PROCESSING}")
                print(f"🔍 Debug - Config.OPENAI_API_KEY exists: {bool(Config.OPENAI_API_KEY)}")
                print(f"🔍 Debug - Environment ENABLE_GPT_PROCESSING: {os.environ.get('ENABLE_GPT_PROCESSING')}")
                print(f"🔍 Debug - Environment OPENAI_API_KEY exists: {bool(os.environ.get('OPENAI_API_KEY'))}")
                
                if Config.ENABLE_GPT_PROCESSING and Config.OPENAI_API_KEY:
                    gpt_processor = GPTDataProcessor()
                    
                    # Check if files have structure issues (like semicolon delimiters)
                    gpt_fixed = False
                    if len(df.columns) == 1 and ';' in str(df.columns[0]):
                        print("🔍 GPT-4 détecte un problème de structure dans le fichier 1...")
                        df = gpt_processor.fix_file_with_gpt_analysis(result1['temp_path'])
                        gpt_fixed = True
                        
                    if len(df2.columns) == 1 and ';' in str(df2.columns[0]):
                        print("🔍 GPT-4 détecte un problème de structure dans le fichier 2...")
                        df2 = gpt_processor.fix_file_with_gpt_analysis(result2['temp_path'])
                        gpt_fixed = True
                    
                    # Apply additional cleaning
                    df = gpt_processor.clean_data_chunk(df)
                    df2 = gpt_processor.clean_data_chunk(df2)
                    
                    if gpt_fixed:
                        print(f"✅ GPT-4 Fix Applied: File1 now has {len(df.columns)} columns, File2 now has {len(df2.columns)} columns")
                        print(f"File1 columns: {df.columns.tolist()[:5]}...")  # Show first 5 columns
                        print(f"File2 columns: {df2.columns.tolist()[:5]}...")  # Show first 5 columns
                        
                        # If we have large files and applied GPT fixes, we need to update the temp files
                        if result1['is_large_file'] and session.get('file1_path'):
                            try:
                                # Save corrected DataFrame back to temp file
                                df.to_csv(session['file1_path'], index=False, encoding='utf-8-sig')
                                print(f"✅ Updated large file 1 temp with GPT corrections")
                            except Exception as e:
                                print(f"⚠️ Could not update large file 1 temp: {e}")
                                
                        if result2['is_large_file'] and session.get('file2_path'):
                            try:
                                # Save corrected DataFrame back to temp file
                                df2.to_csv(session['file2_path'], index=False, encoding='utf-8-sig')
                                print(f"✅ Updated large file 2 temp with GPT corrections")
                            except Exception as e:
                                print(f"⚠️ Could not update large file 2 temp: {e}")
                    
                    flash('🤖 GPT-4 a analysé et corrigé automatiquement la structure des fichiers!', 'success')
                else:
                    flash('⚠️ GPT-4 non configuré - traitement standard appliqué', 'warning')
            except Exception as e:
                flash(f'⚠️ Erreur GPT-4: {str(e)} - traitement standard appliqué', 'warning')
                import traceback
                print(f"GPT Error Details: {traceback.format_exc()}")
        
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

    # DEBUG: Print what we're sending to template
    print(f"🔍 TEMPLATE DEBUG:")
    print(f"File1 columns being sent: {df.columns.tolist()}")
    print(f"File2 columns being sent: {df2.columns.tolist()}")
    print(f"File1 shape: {df.shape}")
    print(f"File2 shape: {df2.shape}")

    return render_template('index.html', 
                            data=df.to_dict(orient='records'), 
                            columns=df.columns.tolist(), 
                            data2=df2.to_dict(orient='records'), 
                            columns2=df2.columns.tolist(),
                            form_action=url_for('comparaison.fast_compare'),
                            is_large_files=session.get('is_large_files', False),
                            file1_info=session.get('file1_info'),
                            file2_info=session.get('file2_info'))

# Debug route to check DataFrame columns after processing
@fichiers_bp.route('/debug_columns')
def debug_columns():
    """Debug route to show current DataFrame columns"""
    import json
    debug_info = {
        'session_data': dict(session),
        'message': 'Check console output for DataFrame details'
    }
    return f"<pre>{json.dumps(debug_info, indent=2, ensure_ascii=False)}</pre>"

# Debug route (remove in production)
@fichiers_bp.route('/debug_session')
def debug_session():
    return f"Session data: {dict(session)}"

@fichiers_bp.route('/download_excel')
def download_excel():
    """Download comparison results as Excel file"""
    try:
        from ..services.generateur_excel import GenerateurExcel
        
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
        
        # DEBUG: Print actual counts from pickle file
        print(f"=== EXCEL DOWNLOAD DEBUG ===")
        print(f"Pickle file path: {temp_path}")
        print(f"Ecarts fichier 1: {len(resultats['ecarts_fichier1'])} rows")
        print(f"Ecarts fichier 2: {len(resultats['ecarts_fichier2'])} rows")
        print(f"Communs: {len(resultats['communs'])} rows")
        print(f"File1 name: {resultats.get('file1_name', 'N/A')}")
        print(f"File2 name: {resultats.get('file2_name', 'N/A')}")
        print(f"===========================")
        
        # Generate Excel file using GenerateurExcel class
        generateur_excel = GenerateurExcel(
            ecarts1=resultats['ecarts_fichier1'],
            ecarts2=resultats['ecarts_fichier2'],
            communs=resultats['communs']
        )
        excel_response = generateur_excel.generer_rapport()
        
        return excel_response
            
    except Exception as e:
        flash(f'Erreur lors du téléchargement: {str(e)}', 'error')
        return redirect(url_for('fichiers.upload_file'))

@fichiers_bp.route('/download_pdf')
def download_pdf():
    """Download comparison results as PDF file"""
    try:
        from ..services.generateur_pdf import GenerateurPdf
        
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
        
        # Generate PDF file using GenerateurPdf class
        generateur_pdf = GenerateurPdf(
            ecarts1=resultats['ecarts_fichier1'],
            ecarts2=resultats['ecarts_fichier2'],
            file1_name=session.get('file1_name', 'Fichier 1'),
            file2_name=session.get('file2_name', 'Fichier 2'),
            total1=resultats.get('total1', len(resultats['ecarts_fichier1'])),
            total2=resultats.get('total2', len(resultats['ecarts_fichier2'])),
            communes=len(resultats['communs'])
        )
        pdf_response = generateur_pdf.generer_pdf()
        
        return pdf_response
            
    except Exception as e:
        flash(f'Erreur lors du téléchargement: {str(e)}', 'error')
        return redirect(url_for('fichiers.upload_file'))
