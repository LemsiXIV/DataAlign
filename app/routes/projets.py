from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from app import db
from app.models import Projet
from app.models.statistiques import StatistiqueEcart
from app.models.fichier_genere import FichierGenere
from app.models.logs import LogExecution
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
    """Route pour afficher le dashboard avec l'arborescence des projets"""
    # Récupérer tous les projets avec leurs fichiers générés
    projets = Projet.query.order_by(Projet.nom_projet, Projet.date_creation.desc()).all()
    stats = StatistiqueEcart.query.all()
    
    # Organiser les projets en arborescence avec leurs traitements
    projets_tree = defaultdict(list)
    
    for projet in projets:
        # S'assurer que le nom du projet est bien une string et pas None
        nom_projet = projet.nom_projet if projet.nom_projet else f"Projet_ID_{projet.id}"
        
        # Récupérer tous les fichiers générés pour ce projet avec gestion d'erreur
        try:
            fichiers_generes = FichierGenere.query.filter_by(projet_id=projet.id).order_by(FichierGenere.date_execution.desc()).all()
        except Exception as e:
            print(f"Erreur lors de la récupération des fichiers générés: {e}")
            fichiers_generes = []
        
        # Si aucun fichier généré, vérifier quand même les fichiers dans l'archive
        if not fichiers_generes and projet.emplacement_archive and os.path.exists(projet.emplacement_archive):
            # Créer un traitement "par défaut" basé sur les fichiers existants
            excel_path = os.path.join(projet.emplacement_archive, "rapport_comparaison.xlsx")
            pdf_path = os.path.join(projet.emplacement_archive, "rapport_comparaison.pdf")
            chart_path = os.path.join(projet.emplacement_archive, "pie_chart.png")
            
            has_excel = os.path.exists(excel_path)
            has_pdf = os.path.exists(pdf_path)
            has_chart = os.path.exists(chart_path)
            
            if has_excel or has_pdf or has_chart:
                projets_tree[nom_projet].append({
                    'id': f"default_{projet.id}",
                    'nom_traitement': "Traitement principal",
                    'date_creation': projet.date_creation,
                    'fichier_1': projet.fichier_1 or "Non défini",
                    'fichier_2': projet.fichier_2 or "Non défini", 
                    'emplacement_archive': projet.emplacement_archive or "Non défini",
                    'formatted_date': projet.date_creation.strftime("%d/%m/%Y à %H:%M:%S") if projet.date_creation else "Date inconnue",
                    'has_excel': has_excel,
                    'has_pdf': has_pdf,
                    'has_chart': has_chart,
                    'has_files': has_excel or has_pdf or has_chart,
                    'projet_id': projet.id
                })
        else:
            # Utiliser les fichiers générés de la base de données
            for fichier in fichiers_generes:
                projets_tree[nom_projet].append({
                    'id': fichier.id,
                    'nom_traitement': fichier.nom_traitement_projet or f"Traitement {fichier.id}",
                    'date_creation': projet.date_creation,
                    'fichier_1': projet.fichier_1 or "Non défini",
                    'fichier_2': projet.fichier_2 or "Non défini", 
                    'emplacement_archive': projet.emplacement_archive or "Non défini",
                    'formatted_date': fichier.date_execution.strftime("%d/%m/%Y à %H:%M:%S") if fichier.date_execution else "Date inconnue",
                    'has_excel': bool(fichier.nom_fichier_excel),
                    'has_pdf': bool(fichier.nom_fichier_pdf),
                    'has_chart': bool(fichier.nom_fichier_graphe),
                    'has_files': bool(fichier.nom_fichier_excel or fichier.nom_fichier_pdf or fichier.nom_fichier_graphe),
                    'projet_id': projet.id
                })
        
        # Si aucun traitement n'existe du tout, afficher le projet sans traitement
        if nom_projet not in projets_tree:
            projets_tree[nom_projet] = []
    
    return render_template('Dashboard.html', projets_tree=dict(projets_tree), stats=stats)

@projets_bp.route('/projet-details/<int:projet_id>')
def projet_details(projet_id):
    """Route pour afficher les détails d'un projet spécifique dans une popup"""
    projet = Projet.query.get_or_404(projet_id)
    
    # Vérifier si les fichiers de rapport existent dans le dossier archive
    rapport_excel_path = None
    rapport_pdf_path = None
    chart_path = None
    has_files_to_download = False
    
    # Rechercher les statistiques pour ce projet
    stats = StatistiqueEcart.query.filter_by(projet_id=projet_id).first()
    
    if projet.emplacement_archive and os.path.exists(projet.emplacement_archive):
        excel_path = os.path.join(projet.emplacement_archive, "rapport_comparaison.xlsx")
        pdf_path = os.path.join(projet.emplacement_archive, "rapport_comparaison.pdf")
        chart_file = os.path.join(projet.emplacement_archive, "pie_chart.png")
        
        if os.path.exists(excel_path):
            rapport_excel_path = excel_path
        if os.path.exists(pdf_path):
            rapport_pdf_path = pdf_path
        if os.path.exists(chart_file):
            chart_path = chart_file
            
        # Vérifier s'il y a des fichiers dans le dossier pour le ZIP
        if os.path.isdir(projet.emplacement_archive):
            files_in_dir = [f for f in os.listdir(projet.emplacement_archive) 
                           if os.path.isfile(os.path.join(projet.emplacement_archive, f))]
            has_files_to_download = len(files_in_dir) > 0
    
    # Compiler les informations du projet
    projet_info = {
        'id': projet.id,
        'nom_projet': projet.nom_projet,
        'date_creation': projet.date_creation.strftime("%d/%m/%Y à %H:%M:%S") if projet.date_creation else "N/A",
        'fichier_1': projet.fichier_1 or "Non défini",
        'fichier_2': projet.fichier_2 or "Non défini",
        'emplacement_archive': projet.emplacement_archive or "Non défini",
        'has_excel': rapport_excel_path is not None,
        'has_pdf': rapport_pdf_path is not None,
        'has_chart': chart_path is not None,
        'has_files_to_download': has_files_to_download,
        'statistics': {
            'fichier1_unique': stats.fichier1_unique if stats else 0,
            'fichier2_unique': stats.fichier2_unique if stats else 0,
            'communs': stats.communs if stats else 0,
            'total_ecarts': (stats.fichier1_unique + stats.fichier2_unique) if stats else 0,
            'date_execution': stats.date_execution.strftime("%d/%m/%Y à %H:%M:%S") if stats and stats.date_execution else "N/A"
        }
    }
    
    return jsonify(projet_info)

@projets_bp.route('/projet-chart/<int:projet_id>')
def projet_chart(projet_id):
    """Route pour servir le graphique d'un projet spécifique"""
    projet = Projet.query.get_or_404(projet_id)
    
    if not projet.emplacement_archive or not os.path.exists(projet.emplacement_archive):
        return jsonify({'error': 'Archive introuvable'}), 404
    
    chart_path = os.path.join(projet.emplacement_archive, "pie_chart.png")
    
    if not os.path.exists(chart_path):
        return jsonify({'error': 'Graphique introuvable'}), 404
    
    return send_file(chart_path, mimetype='image/png')

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

@projets_bp.route('/logs')
def logs():
    """Route pour consulter les logs de nettoyage et autres opérations"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filtrer par type de log
    log_type = request.args.get('type', 'all')
    
    query = LogExecution.query
    
    if log_type == 'cleanup':
        query = query.filter(LogExecution.message.like('%Nettoyage%'))
    elif log_type == 'errors':
        query = query.filter(LogExecution.statut == 'échec')
    elif log_type == 'success':
        query = query.filter(LogExecution.statut == 'succès')
    
    logs = query.order_by(LogExecution.date_execution.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('logs.html', logs=logs, log_type=log_type)

@projets_bp.route('/logs/cleanup')
def cleanup_logs():
    """Route pour consulter tous les logs avec filtres avancés"""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # Filtres disponibles
    status_filter = request.args.get('status')  # succès, échec
    log_type_filter = request.args.get('log_type')  # cleanup, projects, reports, tests
    date_filter = request.args.get('date_range')  # today, week, month
    
    query = LogExecution.query
    
    # Filtre par statut
    if status_filter:
        query = query.filter(LogExecution.statut == status_filter)
    
    # Filtre par type de log
    if log_type_filter == 'cleanup':
        query = query.filter(LogExecution.message.like('%Nettoyage%'))
    elif log_type_filter == 'projects':
        query = query.filter(
            db.or_(
                LogExecution.message.like('%projet créé%'),
                LogExecution.message.like('%projet existant%'),
                LogExecution.message.like('%Fichiers traités%')
            )
        )
    elif log_type_filter == 'reports':
        query = query.filter(
            db.or_(
                LogExecution.message.like('%Excel%'),
                LogExecution.message.like('%PDF%')
            )
        )
    elif log_type_filter == 'tests':
        query = query.filter(LogExecution.message.like('%Test rapide%'))
    
    # Filtre par date
    if date_filter == 'today':
        from datetime import date
        today = date.today()
        query = query.filter(db.func.date(LogExecution.date_execution) == today)
    elif date_filter == 'week':
        from datetime import date, timedelta
        week_ago = date.today() - timedelta(days=7)
        query = query.filter(LogExecution.date_execution >= week_ago)
    elif date_filter == 'month':
        from datetime import date, timedelta
        month_ago = date.today() - timedelta(days=30)
        query = query.filter(LogExecution.date_execution >= month_ago)
    
    logs = query.order_by(LogExecution.date_execution.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiques pour affichage
    total_logs = LogExecution.query.count()
    success_logs = LogExecution.query.filter(LogExecution.statut == 'succès').count()
    error_logs = LogExecution.query.filter(LogExecution.statut == 'échec').count()
    cleanup_logs_count = LogExecution.query.filter(LogExecution.message.like('%Nettoyage%')).count()
    
    stats = {
        'total': total_logs,
        'success': success_logs,
        'errors': error_logs,
        'cleanup': cleanup_logs_count
    }
    
    return render_template('all_logs.html', 
                         logs=logs, 
                         stats=stats,
                         current_filters={
                             'status': status_filter,
                             'log_type': log_type_filter,
                             'date_range': date_filter
                         })
