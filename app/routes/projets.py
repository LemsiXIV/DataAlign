from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from app import db
from app.models import Projet, StatistiqueEcart
from datetime import datetime
import os
import zipfile
import tempfile
from collections import defaultdict

projets_bp = Blueprint('projets', __name__)

@projets_bp.route("/")
@projets_bp.route("/app/templates/index")
def index():
    projets = Projet.query.order_by(Projet.date_creation.desc()).all()
    return render_template('index.html', projets=projets)



@projets_bp.route('/dashboard')
def dashboard():
    # Récupérer tous les projets avec leurs informations
    projets = Projet.query.order_by(Projet.nom_projet, Projet.date_creation.desc()).all()
    stats = StatistiqueEcart.query.all()
    
    # Debug: Afficher tous les projets pour vérifier
    print("=== DEBUG PROJETS ===")
    print(f"Nombre total de projets: {len(projets)}")
    for projet in projets:
        print(f"ID: {projet.id}, Nom: '{projet.nom_projet}', Date: {projet.date_creation}, Archive: {projet.emplacement_archive}")
    
    # Organiser les projets par nom avec leurs sous-traitements
    projets_tree = defaultdict(list)
    for projet in projets:
        # Formater la date avec heure pour le debug
        if projet.date_creation:
            formatted_date_with_time = projet.date_creation.strftime("%d/%m/%Y à %H:%M")
        else:
            formatted_date_with_time = "Date inconnue"
        
        # S'assurer que le nom du projet est bien une string et pas None
        nom_projet = projet.nom_projet if projet.nom_projet else f"Projet_ID_{projet.id}"
        
        projets_tree[nom_projet].append({
            'id': projet.id,
            'date_creation': projet.date_creation,
            'fichier_1': projet.fichier_1 or "Non défini",
            'fichier_2': projet.fichier_2 or "Non défini", 
            'emplacement_archive': projet.emplacement_archive or "Non défini",
            'formatted_date': formatted_date_with_time
        })
    
    # Debug: Afficher l'arborescence
    print("=== DEBUG ARBORESCENCE ===")
    for nom_projet, traitements in projets_tree.items():
        print(f"Projet: '{nom_projet}' - {len(traitements)} traitement(s)")
        for i, traitement in enumerate(traitements, 1):
            print(f"  {i}. ID: {traitement['id']}, Date: {traitement['formatted_date']}")
    
    return render_template('Dashboard.html', projets_tree=dict(projets_tree), stats=stats)

@projets_bp.route('/projet-details/<int:projet_id>')
def projet_details(projet_id):
    """Route pour afficher les détails d'un projet spécifique dans une popup"""
    projet = Projet.query.get_or_404(projet_id)
    
    # Vérifier si les fichiers de rapport existent dans le dossier archive
    rapport_excel_path = None
    rapport_pdf_path = None
    has_files_to_download = False
    
    if projet.emplacement_archive and os.path.exists(projet.emplacement_archive):
        excel_path = os.path.join(projet.emplacement_archive, "rapport_comparaison.xlsx")
        pdf_path = os.path.join(projet.emplacement_archive, "rapport_comparaison.pdf")
        
        if os.path.exists(excel_path):
            rapport_excel_path = excel_path
        if os.path.exists(pdf_path):
            rapport_pdf_path = pdf_path
            
        # Vérifier s'il y a des fichiers dans le dossier pour le ZIP
        if os.path.isdir(projet.emplacement_archive):
            files_in_dir = [f for f in os.listdir(projet.emplacement_archive) 
                           if os.path.isfile(os.path.join(projet.emplacement_archive, f))]
            has_files_to_download = len(files_in_dir) > 0
    
    projet_info = {
        'id': projet.id,
        'nom_projet': projet.nom_projet,
        'date_creation': projet.date_creation.strftime("%d/%m/%Y %H:%M") if projet.date_creation else "N/A",
        'fichier_1': projet.fichier_1,
        'fichier_2': projet.fichier_2,
        'emplacement_archive': projet.emplacement_archive,
        'has_excel': rapport_excel_path is not None,
        'has_pdf': rapport_pdf_path is not None,
        'has_files_to_download': has_files_to_download
    }
    
    return jsonify(projet_info)

@projets_bp.route('/download-project-zip/<int:projet_id>')
def download_project_zip(projet_id):
    """Route pour télécharger tout le contenu d'un projet spécifique en ZIP"""
    projet = Projet.query.get_or_404(projet_id)
    
    if not projet.emplacement_archive or not os.path.exists(projet.emplacement_archive):
        flash("Dossier d'archive introuvable", "error")
        return redirect(url_for('projets.dashboard'))
    
    # Créer un fichier ZIP temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        zip_path = tmp_file.name
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Vérifier si emplacement_archive est un dossier ou un chemin
            if os.path.isdir(projet.emplacement_archive):
                # Ajouter seulement les fichiers du dossier spécifique (pas les sous-dossiers)
                for file in os.listdir(projet.emplacement_archive):
                    file_path = os.path.join(projet.emplacement_archive, file)
                    # Ajouter seulement les fichiers (pas les dossiers)
                    if os.path.isfile(file_path):
                        zipf.write(file_path, file)
            else:
                flash("L'emplacement d'archive n'est pas un dossier valide", "error")
                return redirect(url_for('projets.dashboard'))
        
        # Nom du fichier ZIP avec le nom du projet et la date de création
        date_str = projet.date_creation.strftime('%Y%m%d_%H%M%S') if projet.date_creation else 'unknown'
        zip_filename = f"{projet.nom_projet}_{date_str}.zip"
        
        return send_file(zip_path, 
                        as_attachment=True, 
                        download_name=zip_filename,
                        mimetype='application/zip')
    
    except Exception as e:
        flash(f"Erreur lors de la création du ZIP : {e}", "error")
        return redirect(url_for('projets.dashboard'))
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except:
                pass

@projets_bp.route('/download-report-file/<int:projet_id>/<filename>')
def download_report_file(projet_id, filename):
    """Route pour télécharger un fichier de rapport spécifique"""
    projet = Projet.query.get_or_404(projet_id)
    
    if not projet.emplacement_archive or not os.path.exists(projet.emplacement_archive):
        flash("Dossier d'archive introuvable", "error")
        return redirect(url_for('projets.dashboard'))
    
    file_path = os.path.join(projet.emplacement_archive, filename)
    
    if not os.path.exists(file_path):
        flash("Fichier introuvable", "error")
        return redirect(url_for('projets.dashboard'))
    
    return send_file(file_path, as_attachment=True, download_name=filename)
