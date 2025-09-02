from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from io import StringIO
import pandas as pd
import os
from app import db
from app.models import Projet, ConfigurationCleComposee, StatistiqueEcart
from app.models.logs import LogExecution
from app.models.fichier_genere import FichierGenere
from app.services.comparateur import ComparateurFichiers
from app.services.comparateur_optimise import ComparateurFichiersOptimise, compare_large_files
from app.services.comparateur_mysql_integre import ComparateurFichiersAvecMySQL, comparer_fichiers_avec_mysql
from app.services.generateur_excel import GenerateurExcel
from app.services.generateur_pdf import GenerateurPdf
from datetime import datetime, timedelta
import glob

comparaison_bp = Blueprint('comparaison', __name__)

def cleanup_old_temp_files(temp_dir, max_age_hours=24):
    """Clean up temporary comparison files older than max_age_hours"""
    try:
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        # Find all comparison result files
        pattern = os.path.join(temp_dir, "comparison_results_*.pkl")
        for file_path in glob.glob(pattern):
            try:
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    print(f"Cleaned up old temp file: {file_path}")
            except OSError:
                # File might have been deleted by another process
                pass
    except Exception as e:
        print(f"Error during temp file cleanup: {e}")

@comparaison_bp.route('/compare', methods=['POST'])
def compare():
    keys1 = [k.strip() for k in request.form.getlist('key1')]
    keys2 = [k.strip() for k in request.form.getlist('key2')]

    # Validation des clés
    if not keys1 or not keys2:
        flash("Veuillez sélectionner au moins une clé dans chaque fichier.", "error")
        return redirect(url_for('projets.index'))

    # 🔍 LOGS de débogage
    print("Clés sélectionnées fichier 1 :", keys1)
    print("Clés sélectionnées fichier 2 :", keys2)

    # Get project ID from session (may be None for fast tests)
    projet_id = session.get("projet_id")
    
    # Determine if this is a fast test or a regular project comparison
    is_fast_test = projet_id is None
    
    if not is_fast_test and not projet_id:
        flash("Aucun projet sélectionné. Veuillez sélectionner un projet avant de comparer.", "error")
        return redirect(url_for('projets.index'))

    # Check if we're dealing with large files
    is_large_files = session.get('is_large_files', False)
    
    if is_large_files:
        # Use MySQL-integrated comparison for large files
        file1_path = session.get('file1_path')
        file2_path = session.get('file2_path')
        
        if not file1_path or not file2_path:
            flash("Chemins des fichiers non trouvés pour la comparaison optimisée.", "error")
            return redirect(url_for('projets.index'))
        
        print("Using MySQL-integrated comparison for large files...")
        try:
            # Use the MySQL-integrated comparator that saves results automatically
            results = comparer_fichiers_avec_mysql(
                file1_path=file1_path,
                file2_path=file2_path,
                keys1=keys1,
                keys2=keys2,
                projet_id=projet_id if not is_fast_test else None,
                chunk_size=5000,
                sample_size=50000,  # Increased from 1000 to 50000 for full results
                use_mysql_temp=False  # Use SQLite for temp processing, MySQL for persistence
            )
            
        except Exception as e:
            flash(f"Erreur lors de la comparaison optimisée : {e}", "error")
            return redirect(url_for('projets.index'))
    
    else:
        # Use regular comparison for smaller files
        try:
            df = pd.read_json(session['df_path'])
            df2 = pd.read_json(session['df2_path'])
        except Exception as e:
            flash(f"Erreur lors du chargement des fichiers JSON : {e}", "error")
            return redirect(url_for('projets.index'))

        # Nettoyer les noms de colonnes
        df.columns = df.columns.str.strip()
        df2.columns = df2.columns.str.strip()

        # Use the comparator service
        comparateur = ComparateurFichiers(df, df2, keys1, keys2)
        results = comparateur.comparer()
        
        # Save configurations and statistics to MySQL manually for regular comparison (only if not fast test)
        if not is_fast_test and projet_id:
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

    file1_name = session.get('file1_name', 'Fichier 1')
    file2_name = session.get('file2_name', 'Fichier 2')

    # Auto-generate Excel and PDF files and save them to archive (only for non-fast tests)
    # Check if auto PDF generation is enabled (enabled by default for dashboard access)
    auto_pdf_enabled = os.getenv('AUTO_PDF_GENERATION', 'true').lower() == 'true'
    
    if not is_fast_test and projet_id:
        project_folder = session.get('project_folder')
        
        # If project_folder not in session, get it from database
        if not project_folder and projet_id:
            projet = Projet.query.get(projet_id)
            if projet and projet.emplacement_archive:
                project_folder = projet.emplacement_archive
        
        if project_folder and os.path.exists(project_folder):
            try:
                # Create unique treatment folder with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                treatment_folder = os.path.join(project_folder, f"treatment_{timestamp}")
                
                # Create the treatment folder if it doesn't exist
                os.makedirs(treatment_folder, exist_ok=True)
                
                # Generate Excel file
                generateur_excel = GenerateurExcel(
                    results['ecarts_fichier1'], 
                    results['ecarts_fichier2'], 
                    results['communs'],
                    treatment_folder  # Save to treatment folder instead of project folder
                )
                
                # Save Excel file to treatment folder
                excel_filename = f"rapport_comparaison_{timestamp}.xlsx"
                excel_path = os.path.join(treatment_folder, excel_filename)
                generateur_excel.generer_rapport_fichier(excel_path)
                
                # Initialize PDF-related variables
                pdf_filename = None
                pdf_path = None
                relative_pdf_path = None
                relative_chart_path = None
                
                # Generate PDF file only if enabled (to prevent Docker worker timeouts)
                if auto_pdf_enabled:
                    try:
                        # For large files, use file info from session
                        if is_large_files:
                            file1_size = session.get('file1_info', {}).get('total_rows', 0)
                            file2_size = session.get('file2_info', {}).get('total_rows', 0)
                        else:
                            # For regular files, use dataframe lengths
                            file1_size = len(df) if 'df' in locals() else 0
                            file2_size = len(df2) if 'df2' in locals() else 0
                    except:
                        file1_size = 0
                        file2_size = 0
                    
                    try:
                        print(f"Starting PDF generation for treatment {timestamp}...")
                        
                        generateur_pdf = GenerateurPdf(
                            results['ecarts_fichier1'],
                            results['ecarts_fichier2'],
                            file1_name,
                            file2_name,
                            file1_size,
                            file2_size,
                            results['n_common'],
                            treatment_folder  # Save to treatment folder instead of project folder
                        )
                        
                        # Save PDF file to treatment folder
                        pdf_filename = f"rapport_comparaison_{timestamp}.pdf"
                        pdf_path = os.path.join(treatment_folder, pdf_filename)
                        
                        # Generate PDF with error handling
                        generateur_pdf.generer_pdf_fichier(pdf_path)
                        
                        # Verify PDF was created successfully
                        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                            print(f"PDF generated successfully: {pdf_path}")
                        else:
                            print(f"PDF generation failed or file is empty: {pdf_path}")
                            pdf_filename = None
                            pdf_path = None
                        
                        # Ensure chart file exists in treatment folder
                        chart_filename = "pie_chart.png"
                        chart_path = os.path.join(treatment_folder, chart_filename)
                        
                        # Check if chart was created by PDF generator
                        if not os.path.exists(chart_path):
                            print(f"DEBUG: Chart not found at {chart_path}, checking other locations...")
                            # Try to find chart in current directory or project folder
                            possible_chart_locations = [
                                os.path.join(os.getcwd(), "pie_chart.png"),
                                os.path.join(project_folder, "pie_chart.png"),
                                "pie_chart.png"
                            ]
                            
                            for possible_location in possible_chart_locations:
                                if os.path.exists(possible_location):
                                    print(f"DEBUG: Found chart at {possible_location}, copying to {chart_path}")
                                    import shutil
                                    shutil.copy2(possible_location, chart_path)
                                    break
                            else:
                                print(f"DEBUG: No chart file found in any expected location")
                        
                        # Set PDF paths for database storage
                        if pdf_filename:
                            relative_pdf_path = f"treatment_{timestamp}/{pdf_filename}"
                            relative_chart_path = f"treatment_{timestamp}/pie_chart.png"
                        
                        # Clean up matplotlib resources to prevent threading issues
                        GenerateurPdf.cleanup_matplotlib()
                        
                        print(f"PDF generation completed for treatment {timestamp}")
                        
                    except Exception as pdf_error:
                        print(f"Error during PDF generation: {pdf_error}")
                        # Reset PDF variables on error
                        pdf_filename = None
                        pdf_path = None
                        relative_pdf_path = None
                        relative_chart_path = None
                        
                        # Clean up matplotlib resources even on error
                        try:
                            GenerateurPdf.cleanup_matplotlib()
                        except:
                            pass
                        
                        # Log the PDF error but don't fail the entire comparison
                        log = LogExecution(
                            projet_id=projet_id,
                            statut='avertissement',
                            message=f"PDF generation failed but Excel generated successfully: {str(pdf_error)}"
                        )
                        db.session.add(log)
                
                else:
                    print("PDF generation disabled via environment variable")
                
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
                    # Create unique treatment name using the same timestamp
                    nom_traitement = f"Traitement_{timestamp}"
                    
                    # Store the relative paths from the project archive folder
                    relative_excel_path = f"treatment_{timestamp}/{excel_filename}"
                    
                    # Create relative paths for PDF and chart (should be available with auto-generation)
                    relative_pdf_path = f"treatment_{timestamp}/{pdf_filename}" if pdf_filename else None
                    relative_chart_path = f"treatment_{timestamp}/pie_chart.png" if auto_pdf_enabled else None
                    
                    # Always create new treatment record with unique archive path and relative file paths
                    fichier_genere = FichierGenere(
                        projet_id=projet_id,
                        nom_traitement_projet=nom_traitement,
                        nom_fichier_excel=relative_excel_path,
                        nom_fichier_pdf=relative_pdf_path,
                        nom_fichier_graphe=relative_chart_path,
                        chemin_archive=treatment_folder,
                        date_execution=datetime.now()
                    )
                    db.session.add(fichier_genere)
                
                db.session.commit()
                
                # Add flash message based on what was generated
                if auto_pdf_enabled and pdf_path and os.path.exists(pdf_path):
                    flash(f"Rapport de comparaison terminé ! Les fichiers Excel et PDF ont été automatiquement sauvegardés dans le dossier d'archive du projet.", "success")
                else:
                    flash(f"Rapport de comparaison terminé ! Le fichier Excel a été automatiquement sauvegardé dans le dossier d'archive du projet.", "success")
                
            except Exception as e:
                # Clean up matplotlib resources even in case of error
                GenerateurPdf.cleanup_matplotlib()
                
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
    
    else:
        # For fast tests, just show a simple success message
        if is_fast_test:
            flash("Comparaison rapide terminée ! Utilisez les boutons de téléchargement si vous souhaitez sauvegarder les résultats.", "info")

    # Limit displayed results for performance (show only first 50 rows)
    max_display_rows = 50
    ecarts1_display = results['ecarts_fichier1'].head(max_display_rows).to_dict(orient='records')
    ecarts2_display = results['ecarts_fichier2'].head(max_display_rows).to_dict(orient='records')
    communs_display = results['communs'].head(max_display_rows).to_dict(orient='records')
    
    # Add info about truncated results
    ecarts1_total = len(results['ecarts_fichier1'])
    ecarts2_total = len(results['ecarts_fichier2'])
    communs_total = len(results['communs'])
    
    # Create filtered results without the DataFrame objects to avoid conflicts
    # Only include simple types that are JSON serializable
    filtered_results = {
        'total': results.get('total', 0),
        'n1': results.get('n1', 0),
        'n2': results.get('n2', 0),
        'n_common': results.get('n_common', 0),
        'total_ecarts': results.get('total_ecarts', 0),
        'nb_df': results.get('nb_df', 0),
        'nb_df2': results.get('nb_df2', 0),
        'pct1': results.get('pct1', 0),
        'pct2': results.get('pct2', 0),
        'pct_both': results.get('pct_both', 0)
    }
    
    # Store DataFrames in temporary files for download routes (avoid session size issues)
    import tempfile
    import pickle
    import uuid
    
    # Create temporary file for download results in persistent temp directory
    # Use app/temp directory which is mounted as a volume in Docker
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate unique filename
    temp_filename = f"comparison_results_{uuid.uuid4().hex}.pkl"
    temp_path = os.path.join(temp_dir, temp_filename)
    temp_results = {
        'ecarts_fichier1': results['ecarts_fichier1'],
        'ecarts_fichier2': results['ecarts_fichier2'],
        'communs': results['communs'],
        'file1_name': session.get('file1_name', 'Fichier 1'),
        'file2_name': session.get('file2_name', 'Fichier 2'),
        'total1': results.get('nb_df', 0),
        'total2': results.get('nb_df2', 0)
    }
    
    # Write pickle file to persistent temp directory
    with open(temp_path, 'wb') as temp_file:
        pickle.dump(temp_results, temp_file)
    
    # Store only the file path in session (JSON serializable)
    session['download_results_path'] = temp_path
    session['resultats_comparaison'] = filtered_results  # Only stats, not DataFrames
    
    # DEBUG: Print what we're saving to pickle - COMPARE FUNCTION
    print(f"=== COMPARISON SAVE DEBUG (COMPARE) ===")
    print(f"Saved to pickle: {temp_path}")
    print(f"Ecarts fichier 1: {ecarts1_total} rows")
    print(f"Ecarts fichier 2: {ecarts2_total} rows") 
    print(f"Communs: {communs_total} rows")
    print(f"Web display counts: {ecarts1_total}, {ecarts2_total}, {communs_total}")
    print(f"=======================================")
    
    # Cleanup old temp files
    cleanup_old_temp_files(temp_dir)
    
    return render_template("compare.html",
                           key1=' + '.join(keys1),
                           key2=' + '.join(keys2),
                           ecarts1=ecarts1_display,
                           ecarts2=ecarts2_display,
                           communs=communs_display,
                           ecarts1_total=ecarts1_total,
                           ecarts2_total=ecarts2_total,
                           communs_total=communs_total,
                           max_display_rows=max_display_rows,
                           file1_name=file1_name,
                           file2_name=file2_name,
                           **filtered_results)

@comparaison_bp.route('/Fast_Compare', methods=['POST'])
def fast_compare():
    keys1 = [k.strip() for k in request.form.getlist('key1')]
    keys2 = [k.strip() for k in request.form.getlist('key2')]

    if not keys1 or not keys2:
        flash("Veuillez sélectionner au moins une clé dans chaque fichier.", "error")
        return redirect(url_for('projets.index'))

    # Check if we're dealing with large files
    is_large_files = session.get('is_large_files', False)
    
    if is_large_files:
        # Use optimized comparison for large files (no project ID for fast test)
        file1_path = session.get('file1_path')
        file2_path = session.get('file2_path')
        
        if not file1_path or not file2_path:
            flash("Chemins des fichiers non trouvés pour la comparaison optimisée.", "error")
            return redirect(url_for('projets.index'))
        
        print("Using optimized fast comparison for large files...")
        try:
            # Use optimized comparator with smaller sample for fast comparison
            results = comparer_fichiers_avec_mysql(
                file1_path=file1_path,
                file2_path=file2_path,
                keys1=keys1,
                keys2=keys2,
                projet_id=None,  # No project for fast tests
                chunk_size=3000,  # Smaller chunks for faster processing
                sample_size=5000,  # Increased from 500 to 5000 for better fast test results
                use_mysql_temp=False
            )
            
        except Exception as e:
            flash(f"Erreur lors de la comparaison rapide optimisée : {e}", "error")
            return redirect(url_for('projets.index'))
    
    else:
        # Use regular comparison for smaller files
        try:
            df = pd.read_json(session['df_path'])
            df2 = pd.read_json(session['df2_path'])
        except Exception as e:
            flash(f"Erreur lors de la lecture des fichiers JSON : {e}", "error")
            return redirect(url_for('projets.index'))

        # Nettoyer colonnes
        df.columns = df.columns.str.strip()
        df2.columns = df2.columns.str.strip()

        if not all(k in df.columns for k in keys1) or not all(k in df2.columns for k in keys2):
            flash("Clés invalides sélectionnées.", "error")
            return redirect(url_for('projets.index'))

        # Appeler ton comparateur personnalisé
        comparateur = ComparateurFichiers(df, df2, keys1, keys2)
        results = comparateur.comparer()

    # Limit displayed results for performance (show only first 50 rows)
    max_display_rows = 50
    ecarts1_display = results['ecarts_fichier1'].head(max_display_rows).to_dict(orient='records')
    ecarts2_display = results['ecarts_fichier2'].head(max_display_rows).to_dict(orient='records')
    communs_display = results['communs'].head(max_display_rows).to_dict(orient='records')
    
    # Add info about truncated results
    ecarts1_total = len(results['ecarts_fichier1'])
    ecarts2_total = len(results['ecarts_fichier2'])
    communs_total = len(results['communs'])
    
    # Create filtered results without the DataFrame objects to avoid conflicts
    # Only include simple types that are JSON serializable
    filtered_results = {
        'total': results.get('total', 0),
        'n1': results.get('n1', 0),
        'n2': results.get('n2', 0),
        'n_common': results.get('n_common', 0),
        'total_ecarts': results.get('total_ecarts', 0),
        'nb_df': results.get('nb_df', 0),
        'nb_df2': results.get('nb_df2', 0),
        'pct1': results.get('pct1', 0),
        'pct2': results.get('pct2', 0),
        'pct_both': results.get('pct_both', 0)
    }

    # Store DataFrames in temporary files for download routes (avoid session size issues)
    import tempfile
    import pickle
    import uuid
    
    # Create temporary file for download results in persistent temp directory
    # Use app/temp directory which is mounted as a volume in Docker
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate unique filename
    temp_filename = f"comparison_results_{uuid.uuid4().hex}.pkl"
    temp_path = os.path.join(temp_dir, temp_filename)
    temp_results = {
        'ecarts_fichier1': results['ecarts_fichier1'],
        'ecarts_fichier2': results['ecarts_fichier2'],
        'communs': results['communs'],
        'file1_name': session.get('file1_name', 'Fichier 1'),
        'file2_name': session.get('file2_name', 'Fichier 2'),
        'total1': results.get('nb_df', 0),
        'total2': results.get('nb_df2', 0)
    }
    
    # Write pickle file to persistent temp directory
    with open(temp_path, 'wb') as temp_file:
        pickle.dump(temp_results, temp_file)
    
    # Store only the file path in session (JSON serializable)
    session['download_results_path'] = temp_path
    session['resultats_comparaison'] = filtered_results  # Only stats, not DataFrames

    return render_template("compare.html",
                           key1=' + '.join(keys1),
                           key2=' + '.join(keys2),
                           ecarts1=ecarts1_display,
                           ecarts2=ecarts2_display,
                           communs=communs_display,
                           ecarts1_total=ecarts1_total,
                           ecarts2_total=ecarts2_total,
                           communs_total=communs_total,
                           max_display_rows=max_display_rows,
                           file1_name=session.get('file1_name', 'Fichier 1'),
                           file2_name=session.get('file2_name', 'Fichier 2'),
                           **filtered_results)
