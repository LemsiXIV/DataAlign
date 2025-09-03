from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Projet
from app.models.statistiques import StatistiqueEcart
from app.models.fichier_genere import FichierGenere
from app.models.logs import LogExecution
from app.models.user import DeletionRequest, User
from app.routes.notifications import create_notification
from app.utils.file_manager import delete_project_files, get_file_cleanup_summary
from datetime import datetime
import os
import zipfile
import tempfile
from collections import defaultdict

projets_bp = Blueprint('projets', __name__)

def get_absolute_path(relative_path):
    """
    Convertit un chemin relatif en chemin absolu adapté à l'environnement Docker
    """
    if os.path.isabs(relative_path):
        return relative_path
    
    current_dir = os.getcwd()
    # Dans Docker, nous sommes dans /app, donc les uploads sont dans /app/uploads
    if relative_path.startswith('uploads/'):
        return os.path.join('/app', relative_path)
    else:
        # Chemin relatif standard
        return os.path.join(current_dir, relative_path)

def notify_all_admins(title, message, notification_type='info', related_request_id=None):
    """Helper function to notify all admin users"""
    try:
        admin_users = User.query.filter_by(role='admin').all()
        print(f"DEBUG: Found {len(admin_users)} admin users")
        
        for admin in admin_users:
            print(f"DEBUG: Notifying admin {admin.username} (ID: {admin.id})")
            result = create_notification(
                user_id=admin.id,
                title=title,
                message=message,
                notification_type=notification_type,
                related_request_id=related_request_id
            )
            print(f"DEBUG: Notification created for admin {admin.username}: {result is not None}")
            
        print(f"DEBUG: Finished notifying {len(admin_users)} admins")
    except Exception as e:
        print(f"ERROR in notify_all_admins: {e}")
        import traceback
        traceback.print_exc()

@projets_bp.route("/")
@projets_bp.route("/app/templates/index")
def index():
    projets = Projet.query.order_by(Projet.date_creation.desc()).all()
    return render_template('index.html', projets=projets)



@projets_bp.route('/dashboard')
@login_required
def dashboard():
    """Route pour afficher le dashboard avec l'arborescence des projets"""
    # Filtrer les projets selon les permissions utilisateur
    if current_user.is_admin():
        # Administrateur : voir tous les projets
        projets = Projet.query.order_by(Projet.nom_projet, Projet.date_creation.desc()).all()
        stats = StatistiqueEcart.query.all()
    else:
        # Utilisateur normal : voir seulement ses projets
        projets = Projet.query.filter_by(user_id=current_user.id).order_by(Projet.nom_projet, Projet.date_creation.desc()).all()
        # Statistiques seulement pour ses projets
        projet_ids = [p.id for p in projets]
        if projet_ids:
            stats = StatistiqueEcart.query.filter(StatistiqueEcart.projet_id.in_(projet_ids)).all()
        else:
            stats = []
    
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
        if not fichiers_generes and projet.emplacement_archive:
            # Construire le chemin absolu depuis la racine du projet
            if os.path.isabs(projet.emplacement_archive):
                archive_path = projet.emplacement_archive
            else:
                # Méthode pour Docker : partir du répertoire courant
                archive_path = get_absolute_path(projet.emplacement_archive)
            
            if os.path.exists(archive_path):
                # Créer un traitement "par défaut" basé sur les fichiers existants
                excel_path = os.path.join(archive_path, "rapport_comparaison.xlsx")
                pdf_path = os.path.join(archive_path, "rapport_comparaison.pdf")
                chart_path = os.path.join(archive_path, "pie_chart.png")
                
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
                # Vérifier si les fichiers existent réellement
                has_excel_file = False
                has_pdf_file = False
                has_chart_file = False
                
                if fichier.chemin_archive:
                    # Construire le chemin complet vers le dossier du traitement
                    if os.path.isabs(fichier.chemin_archive):
                        treatment_path = fichier.chemin_archive
                    else:
                        treatment_path = get_absolute_path(fichier.chemin_archive)
                    
                    print(f"DEBUG Dashboard: Checking treatment path: {treatment_path}")
                    
                    if os.path.exists(treatment_path):
                        # Vérifier chaque type de fichier
                        if fichier.nom_fichier_excel:
                            # Essayer plusieurs emplacements pour le fichier Excel
                            excel_locations = [
                                os.path.join(treatment_path, os.path.basename(fichier.nom_fichier_excel)),
                                os.path.join(treatment_path, fichier.nom_fichier_excel),
                            ]
                            # Si le nom du fichier contient un sous-dossier, essayer aussi cette structure
                            if '/' in fichier.nom_fichier_excel:
                                excel_locations.append(os.path.join(treatment_path, fichier.nom_fichier_excel))
                            
                            for excel_path in excel_locations:
                                if os.path.exists(excel_path):
                                    has_excel_file = True
                                    print(f"DEBUG Dashboard: Excel found at: {excel_path}")
                                    break
                        
                        if fichier.nom_fichier_pdf:
                            # Essayer plusieurs emplacements pour le fichier PDF
                            pdf_locations = [
                                os.path.join(treatment_path, os.path.basename(fichier.nom_fichier_pdf)),
                                os.path.join(treatment_path, fichier.nom_fichier_pdf),
                            ]
                            if '/' in fichier.nom_fichier_pdf:
                                pdf_locations.append(os.path.join(treatment_path, fichier.nom_fichier_pdf))
                            
                            for pdf_path in pdf_locations:
                                if os.path.exists(pdf_path):
                                    has_pdf_file = True
                                    print(f"DEBUG Dashboard: PDF found at: {pdf_path}")
                                    break
                        
                        if fichier.nom_fichier_graphe:
                            # Essayer plusieurs emplacements pour le fichier graphique
                            chart_locations = [
                                os.path.join(treatment_path, os.path.basename(fichier.nom_fichier_graphe)),
                                os.path.join(treatment_path, fichier.nom_fichier_graphe),
                            ]
                            if '/' in fichier.nom_fichier_graphe:
                                chart_locations.append(os.path.join(treatment_path, fichier.nom_fichier_graphe))
                            
                            for chart_path in chart_locations:
                                if os.path.exists(chart_path):
                                    has_chart_file = True
                                    print(f"DEBUG Dashboard: Chart found at: {chart_path}")
                                    break
                    else:
                        print(f"DEBUG Dashboard: Treatment path does not exist: {treatment_path}")
                
                print(f"DEBUG Dashboard: Treatment {fichier.id} - Excel: {has_excel_file}, PDF: {has_pdf_file}, Chart: {has_chart_file}")
                
                projets_tree[nom_projet].append({
                    'id': fichier.id,
                    'nom_traitement': fichier.nom_traitement_projet or f"Traitement {fichier.id}",
                    'date_creation': projet.date_creation,
                    'fichier_1': projet.fichier_1 or "Non défini",
                    'fichier_2': projet.fichier_2 or "Non défini", 
                    'emplacement_archive': projet.emplacement_archive or "Non défini",
                    'formatted_date': fichier.date_execution.strftime("%d/%m/%Y à %H:%M:%S") if fichier.date_execution else "Date inconnue",
                    'has_excel': has_excel_file,  # Use real file existence
                    'has_pdf': has_pdf_file,      # Use real file existence
                    'has_chart': has_chart_file,  # Use real file existence
                    'has_files': has_excel_file or has_pdf_file or has_chart_file,  # Use real file existence
                    'projet_id': projet.id
                })
        
        # Si aucun traitement n'existe du tout, afficher le projet sans traitement
        if nom_projet not in projets_tree:
            projets_tree[nom_projet] = []
    
    return render_template('Dashboard.html', projets_tree=dict(projets_tree), stats=stats)

@projets_bp.route('/projet-details/<int:projet_id>')
@login_required
def projet_details(projet_id):
    """Route pour afficher les détails d'un projet spécifique dans une popup"""
    try:
        print(f"DEBUG: Début traitement projet ID: {projet_id}")
        
        projet = Projet.query.get_or_404(projet_id)
        
        # Vérifier les permissions : seul le propriétaire ou l'admin peut voir les détails
        if not current_user.is_admin() and projet.user_id != current_user.id:
            return jsonify({
                'error': True,
                'message': 'Accès non autorisé à ce projet'
            }), 403
        
        print(f"DEBUG: Projet trouvé: {projet.nom_projet}")
        
        # Vérifier si les fichiers de rapport existent dans le dossier archive
        rapport_excel_path = None
        rapport_pdf_path = None
        chart_path = None
        has_files_to_download = False
        
        # Rechercher les statistiques pour ce projet avec gestion d'erreur
        try:
            stats = StatistiqueEcart.query.filter_by(projet_id=projet_id).first()
            print(f"DEBUG: Statistiques trouvées: {stats is not None}")
            if stats:
                print(f"DEBUG: Stats détails - Fichier1: {stats.nb_ecarts_uniquement_fichier1}, Fichier2: {stats.nb_ecarts_uniquement_fichier2}, Communs: {stats.nb_ecarts_communs}")
        except Exception as e:
            print(f"ERREUR lors de la récupération des statistiques: {e}")
            stats = None
        
        print(f"DEBUG: Emplacement archive: {projet.emplacement_archive}")
        
        # Construire le chemin absolu depuis la racine du projet
        if projet.emplacement_archive:
            if os.path.isabs(projet.emplacement_archive):
                archive_path = projet.emplacement_archive
            else:
                # Pour Docker, construire le chemin depuis /app
                current_dir = os.getcwd()
                print(f"DEBUG: current_dir={current_dir}")
                
                if '/app' in current_dir:
                    # Nous sommes dans un conteneur Docker
                    app_root = '/app'
                    archive_path = os.path.join(app_root, projet.emplacement_archive)
                else:
                    # Développement local
                    if current_dir.endswith('app'):
                        project_root = os.path.dirname(current_dir)
                    else:
                        project_root = current_dir
                    archive_path = os.path.join(project_root, projet.emplacement_archive)
        else:
            archive_path = None
        
        print(f"DEBUG: Archive path: {archive_path}")
        
        if archive_path and os.path.exists(archive_path):
            print(f"DEBUG: Archive existe, vérification des fichiers...")
            
            # D'abord chercher dans les sous-dossiers treatment_*
            treatment_dirs = []
            try:
                all_items = os.listdir(archive_path)
                treatment_dirs = [d for d in all_items if d.startswith('treatment_') and os.path.isdir(os.path.join(archive_path, d))]
                print(f"DEBUG: Treatment directories found: {treatment_dirs}")
            except Exception as e:
                print(f"DEBUG: Error listing archive directory: {e}")
            
            if treatment_dirs:
                # Prendre le plus récent
                treatment_dir = sorted(treatment_dirs)[-1]
                treatment_path = os.path.join(archive_path, treatment_dir)
                print(f"DEBUG: Using treatment directory: {treatment_path}")
                
                # Chercher les fichiers dans le dossier treatment de manière récursive
                excel_path = None
                pdf_path = None
                chart_file = None
                
                try:
                    # Chercher récursivement dans le dossier treatment et ses sous-dossiers
                    for root, dirs, files in os.walk(treatment_path):
                        print(f"DEBUG: Checking directory: {root}")
                        print(f"DEBUG: Files in directory: {files}")
                        
                        for file in files:
                            file_path = os.path.join(root, file)
                            if file.endswith('.xlsx') and not excel_path:
                                excel_path = file_path
                                print(f"DEBUG: Excel trouvé: {file} at {file_path}")
                            elif file.endswith('.pdf') and not pdf_path:
                                pdf_path = file_path
                                print(f"DEBUG: PDF trouvé: {file} at {file_path}")
                            elif file.endswith('.png') and ('chart' in file.lower() or 'pie' in file.lower()) and not chart_file:
                                chart_file = file_path
                                print(f"DEBUG: Chart trouvé: {file} at {file_path}")
                            
                except Exception as e:
                    print(f"DEBUG: Error reading treatment directory: {e}")
            else:
                # Fallback: chercher directement dans l'archive
                print(f"DEBUG: No treatment directories, checking archive directly")
                excel_path = os.path.join(archive_path, "rapport_comparaison.xlsx")
                pdf_path = os.path.join(archive_path, "rapport_comparaison.pdf")
                chart_file = os.path.join(archive_path, "pie_chart.png")
            
            # Assigner les chemins trouvés
            if excel_path and os.path.exists(excel_path):
                rapport_excel_path = excel_path
                print(f"DEBUG: Excel final: {excel_path}")
            if pdf_path and os.path.exists(pdf_path):
                rapport_pdf_path = pdf_path
                print(f"DEBUG: PDF final: {pdf_path}")
            if chart_file and os.path.exists(chart_file):
                chart_path = chart_file
                print(f"DEBUG: Chart final: {chart_file}")
                
            # Vérifier s'il y a des fichiers dans le dossier pour le ZIP
            if os.path.isdir(archive_path):
                try:
                    files_in_dir = []
                    for root, dirs, files in os.walk(archive_path):
                        files_in_dir.extend([f for f in files if os.path.isfile(os.path.join(root, f))])
                    has_files_to_download = len(files_in_dir) > 0
                    print(f"DEBUG: Fichiers pour ZIP: {len(files_in_dir)}")
                except Exception as e:
                    print(f"DEBUG: Error counting files: {e}")
                    has_files_to_download = False
        else:
            print(f"DEBUG: Archive n'existe pas ou non accessible")
        
        # Compiler les informations du projet
        print(f"DEBUG: Compilation des informations...")
        
        # Tester chaque partie des statistiques de manière ultra-défensive
        fichier1_unique = 0
        fichier2_unique = 0
        communs = 0
        total_ecarts = 0
        date_execution = "N/A"
        
        if stats:
            try:
                # Vérifier que l'attribut existe avant d'y accéder
                if hasattr(stats, 'nb_ecarts_uniquement_fichier1'):
                    fichier1_unique = stats.nb_ecarts_uniquement_fichier1 or 0
                    print(f"DEBUG: fichier1_unique = {fichier1_unique}")
                else:
                    print("ERREUR: Attribut nb_ecarts_uniquement_fichier1 n'existe pas")
            except Exception as e:
                print(f"ERREUR fichier1_unique: {e}")
                
            try:
                if hasattr(stats, 'nb_ecarts_uniquement_fichier2'):
                    fichier2_unique = stats.nb_ecarts_uniquement_fichier2 or 0
                    print(f"DEBUG: fichier2_unique = {fichier2_unique}")
                else:
                    print("ERREUR: Attribut nb_ecarts_uniquement_fichier2 n'existe pas")
            except Exception as e:
                print(f"ERREUR fichier2_unique: {e}")
                
            try:
                if hasattr(stats, 'nb_ecarts_communs'):
                    communs = stats.nb_ecarts_communs or 0
                    print(f"DEBUG: communs = {communs}")
                else:
                    print("ERREUR: Attribut nb_ecarts_communs n'existe pas")
            except Exception as e:
                print(f"ERREUR communs: {e}")
                
            try:
                total_ecarts = fichier1_unique + fichier2_unique
                print(f"DEBUG: total_ecarts = {total_ecarts}")
            except Exception as e:
                print(f"ERREUR total_ecarts: {e}")
                
            try:
                if hasattr(stats, 'date_execution') and stats.date_execution:
                    date_execution = stats.date_execution.strftime("%d/%m/%Y à %H:%M:%S")
                    print(f"DEBUG: date_execution = {date_execution}")
                else:
                    print("DEBUG: Pas de date_execution ou attribut manquant")
            except Exception as e:
                print(f"ERREUR date_execution: {e}")
        
        # Test de création de l'objet projet_info de manière défensive
        try:
            projet_info = {
                'id': projet.id,
                'nom_projet': str(projet.nom_projet) if projet.nom_projet else "Projet sans nom",
                'date_creation': projet.date_creation.strftime("%d/%m/%Y à %H:%M:%S") if projet.date_creation else "N/A",
                'fichier_1': str(projet.fichier_1) if projet.fichier_1 else "Non défini",
                'fichier_2': str(projet.fichier_2) if projet.fichier_2 else "Non défini",
                'emplacement_archive': str(projet.emplacement_archive) if projet.emplacement_archive else "Non défini",
                'has_excel': bool(rapport_excel_path is not None),
                'has_pdf': bool(rapport_pdf_path is not None),
                'has_chart': bool(chart_path is not None),
                'has_files_to_download': bool(has_files_to_download),
                'statistics': {
                    'fichier1_unique': int(fichier1_unique),
                    'fichier2_unique': int(fichier2_unique),
                    'communs': int(communs),
                    'total_ecarts': int(total_ecarts),
                    'date_execution': str(date_execution)
                }
            }
            print(f"DEBUG: projet_info créé avec succès")
        except Exception as e:
            print(f"ERREUR lors de la création de projet_info: {e}")
            raise
        
        print(f"DEBUG: Projet {projet_id} - Données compilées avec succès")
        return jsonify(projet_info)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERREUR COMPLÈTE dans projet_details pour projet {projet_id}:")
        print(error_details)
        
        # Retourner une réponse d'erreur JSON au lieu d'une erreur 500
        return jsonify({
            'error': True,
            'message': f"Erreur lors du chargement des détails: {str(e)}",
            'details': error_details
        }), 500

@projets_bp.route('/project-evolution/<int:project_id>')
@login_required
def project_evolution(project_id):
    """Route pour récupérer l'évolution des statistiques d'un projet"""
    try:
        # Vérifier que le projet existe
        projet = Projet.query.get_or_404(project_id)
        
        # Vérifier les permissions : seul le propriétaire ou l'admin peut voir l'évolution
        if not current_user.is_admin() and projet.user_id != current_user.id:
            return jsonify({
                'error': True,
                'message': 'Accès non autorisé à ce projet'
            }), 403
        
        # Récupérer toutes les statistiques pour ce projet, triées par date
        statistiques = StatistiqueEcart.query.filter_by(projet_id=project_id).order_by(StatistiqueEcart.date_execution.asc()).all()
        
        if not statistiques:
            return jsonify({
                'error': False,
                'message': 'Aucune donnée d\'évolution disponible pour ce projet',
                'dates': [],
                'ecarts_fichier1': [],
                'ecarts_fichier2': [],
                'ecarts_communs': [],
                'total_ecarts': []
            })
        
        # Préparer les données pour le graphique
        dates = []
        ecarts_fichier1 = []
        ecarts_fichier2 = []
        ecarts_communs = []
        total_ecarts = []
        
        for stat in statistiques:
            # Formater la date
            date_str = stat.date_execution.strftime("%d/%m/%Y %H:%M") if stat.date_execution else "N/A"
            dates.append(date_str)
            
            # Ajouter les données (avec valeurs par défaut si None)
            f1_ecarts = stat.nb_ecarts_uniquement_fichier1 or 0
            f2_ecarts = stat.nb_ecarts_uniquement_fichier2 or 0
            communs = stat.nb_ecarts_communs or 0
            
            ecarts_fichier1.append(f1_ecarts)
            ecarts_fichier2.append(f2_ecarts)
            ecarts_communs.append(communs)
            total_ecarts.append(f1_ecarts + f2_ecarts)
        
        return jsonify({
            'error': False,
            'project_name': projet.nom_projet,
            'dates': dates,
            'ecarts_fichier1': ecarts_fichier1,
            'ecarts_fichier2': ecarts_fichier2,
            'ecarts_communs': ecarts_communs,
            'total_ecarts': total_ecarts
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERREUR dans project_evolution pour projet {project_id}:")
        print(error_details)
        
        return jsonify({
            'error': True,
            'message': f"Erreur lors du chargement de l'évolution: {str(e)}",
            'details': error_details
        }), 500

@projets_bp.route('/projet-chart/<int:projet_id>')
@login_required
def projet_chart(projet_id):
    """Route pour servir le graphique d'un projet spécifique (cherche le traitement le plus récent avec graphique)"""
    projet = Projet.query.get_or_404(projet_id)
    
    # Vérifier les permissions : seul le propriétaire ou l'admin peut voir le graphique
    if not current_user.is_admin() and projet.user_id != current_user.id:
        return jsonify({'error': 'Accès non autorisé à ce projet'}), 403
    
    if not projet.emplacement_archive:
        return jsonify({'error': 'Archive introuvable'}), 404
    
    # Construire le chemin absolu depuis la racine du projet
    if os.path.isabs(projet.emplacement_archive):
        archive_path = projet.emplacement_archive
    else:
        # Méthode pour Docker : partir du répertoire courant
        archive_path = get_absolute_path(projet.emplacement_archive)
    
    if not os.path.exists(archive_path):
        return jsonify({'error': f'Archive introuvable: {archive_path}'}), 404
    
    # Try to find chart from the most recent treatment first
    from app.models.fichier_genere import FichierGenere
    recent_treatment = FichierGenere.query.filter_by(projet_id=projet_id)\
                                         .filter(FichierGenere.nom_fichier_graphe.isnot(None))\
                                         .order_by(FichierGenere.date_execution.desc())\
                                         .first()
    
    chart_path = None
    if recent_treatment and recent_treatment.nom_fichier_graphe:
        # New format: chart is in treatment folder with relative path
        if recent_treatment.chemin_archive:
            chart_path = os.path.join(recent_treatment.chemin_archive, os.path.basename(recent_treatment.nom_fichier_graphe))
        else:
            # Fallback: construct path from archive + relative path
            chart_path = os.path.join(archive_path, recent_treatment.nom_fichier_graphe)
    
    # Fallback: look for old format chart in main archive folder
    if not chart_path or not os.path.exists(chart_path):
        old_chart_path = os.path.join(archive_path, "pie_chart.png")
        if os.path.exists(old_chart_path):
            chart_path = old_chart_path
    
    if not chart_path or not os.path.exists(chart_path):
        return jsonify({'error': f'Graphique introuvable pour le projet {projet_id}'}), 404
    
    return send_file(chart_path, mimetype='image/png')

@projets_bp.route('/treatment-chart/<int:treatment_id>')
@login_required
def treatment_chart(treatment_id):
    """Route pour servir le graphique d'un traitement spécifique"""
    from app.models.fichier_genere import FichierGenere
    
    try:
        treatment = FichierGenere.query.get_or_404(treatment_id)
        
        # Vérifier les permissions via le projet parent
        projet = treatment.projet
        if projet and not current_user.is_admin() and projet.user_id != current_user.id:
            return jsonify({'error': 'Accès non autorisé à ce traitement'}), 403
        
        print(f"DEBUG: Treatment found - ID: {treatment_id}, nom_fichier_graphe: {treatment.nom_fichier_graphe}")
        print(f"DEBUG: Treatment chemin_archive: {treatment.chemin_archive}")
        
        if not treatment.nom_fichier_graphe:
            print(f"DEBUG: No chart file specified for treatment {treatment_id}")
            return jsonify({'error': 'Aucun graphique disponible pour ce traitement'}), 404
        
        # Build the full path to the chart
        chart_path = None
        if treatment.chemin_archive:
            # New format: chart is in treatment folder
            # If nom_fichier_graphe contains a path, use just the filename
            if '/' in treatment.nom_fichier_graphe or '\\' in treatment.nom_fichier_graphe:
                chart_filename = os.path.basename(treatment.nom_fichier_graphe)
            else:
                chart_filename = treatment.nom_fichier_graphe
            
            # Ensure we have the correct absolute path
            if os.path.isabs(treatment.chemin_archive):
                chart_path = os.path.join(treatment.chemin_archive, chart_filename)
            else:
                # Pour Docker, nous sommes dans /app
                # chemin_archive est relatif à la racine du projet
                chart_path = os.path.join(get_absolute_path(treatment.chemin_archive), chart_filename)
            
            print(f"DEBUG: New format chart path: {chart_path}")
        else:
            # Fallback: old format
            projet = treatment.projet
            if projet and projet.emplacement_archive:
                if os.path.isabs(projet.emplacement_archive):
                    archive_path = projet.emplacement_archive
                else:
                    current_dir = os.getcwd()
                    # Dans Docker, nous sommes dans /app, donc les uploads sont dans /app/uploads
                    archive_path = get_absolute_path(projet.emplacement_archive)
                
                chart_path = os.path.join(archive_path, treatment.nom_fichier_graphe)
                print(f"DEBUG: Fallback chart path: {chart_path}")
        
        print(f"DEBUG: Final chart path: {chart_path}")
        print(f"DEBUG: Chart path exists: {os.path.exists(chart_path) if chart_path else 'No path'}")
        
        if not chart_path or not os.path.exists(chart_path):
            # Try to find any chart files in the treatment directory for debugging
            if treatment.chemin_archive:
                absolute_treatment_path = get_absolute_path(treatment.chemin_archive)
                print(f"DEBUG: Looking in treatment directory: {absolute_treatment_path}")
                if os.path.exists(absolute_treatment_path):
                    files_in_dir = os.listdir(absolute_treatment_path)
                    print(f"DEBUG: Files in treatment directory: {files_in_dir}")
                else:
                    print(f"DEBUG: Treatment directory does not exist: {absolute_treatment_path}")
            
            return jsonify({'error': f'Graphique introuvable: {chart_path}'}), 404
        
        return send_file(chart_path, mimetype='image/png')
        
    except Exception as e:
        print(f"DEBUG: Error in treatment_chart: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

@projets_bp.route('/download-project-zip/<int:projet_id>')
@login_required
def download_project_zip(projet_id):
    """Route pour télécharger tout le contenu d'un projet spécifique en ZIP"""
    projet = Projet.query.get_or_404(projet_id)
    
    # Vérifier les permissions : seul le propriétaire ou l'admin peut télécharger
    if not current_user.is_admin() and projet.user_id != current_user.id:
        flash("Accès non autorisé à ce projet", "error")
        return redirect(url_for('projets.dashboard'))
    
    if not projet.emplacement_archive:
        flash("Dossier d'archive introuvable", "error")
        return redirect(url_for('projets.dashboard'))
    
    # Construire le chemin absolu depuis la racine du projet
    if os.path.isabs(projet.emplacement_archive):
        archive_path = projet.emplacement_archive
    else:
        # Méthode plus robuste : partir du répertoire courant et remonter si nécessaire
        current_dir = os.getcwd()
        if current_dir.endswith('app'):
            # Si on est dans le dossier app/, remonter d'un niveau
            project_root = os.path.dirname(current_dir)
        else:
            # Sinon, on est déjà à la racine
            project_root = current_dir
        archive_path = os.path.join(project_root, projet.emplacement_archive)
    
    if not os.path.exists(archive_path):
        flash(f"Dossier d'archive introuvable: {archive_path}", "error")
        return redirect(url_for('projets.dashboard'))
    
    # Créer un fichier ZIP temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        zip_path = tmp_file.name
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Vérifier si emplacement_archive est un dossier ou un chemin
            if os.path.isdir(archive_path):
                # Ajouter tous les fichiers et dossiers récursivement
                for root, dirs, files in os.walk(archive_path):
                    # Calculer le chemin relatif depuis archive_path
                    relative_root = os.path.relpath(root, archive_path)
                    
                    # Ajouter tous les fichiers
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Créer le nom d'archive en préservant la structure des dossiers
                        if relative_root == '.':
                            # Fichier à la racine
                            archive_name = file
                        else:
                            # Fichier dans un sous-dossier
                            archive_name = os.path.join(relative_root, file).replace('\\', '/')
                        zipf.write(file_path, archive_name)
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

@projets_bp.route('/download-treatment-zip/<int:treatment_id>')
@login_required
def download_treatment_zip(treatment_id):
    """Route pour télécharger les fichiers d'un traitement spécifique en ZIP"""
    from app.models.fichier_genere import FichierGenere
    
    treatment = FichierGenere.query.get_or_404(treatment_id)
    projet = treatment.projet
    
    # Vérifier les permissions via le projet parent
    if projet and not current_user.is_admin() and projet.user_id != current_user.id:
        flash("Accès non autorisé à ce traitement", "error")
        return redirect(url_for('projets.dashboard'))
    
    if not treatment.chemin_archive:
        flash("Dossier de traitement introuvable", "error")
        return redirect(url_for('projets.dashboard'))
    
    # Construire le chemin absolu du traitement
    if os.path.isabs(treatment.chemin_archive):
        treatment_path = treatment.chemin_archive
    else:
        # Pour Docker, nous sommes dans /app
        # chemin_archive est relatif à la racine du projet
        treatment_path = get_absolute_path(treatment.chemin_archive)
    
    if not os.path.exists(treatment_path):
        flash(f"Dossier de traitement introuvable: {treatment_path}", "error")
        return redirect(url_for('projets.dashboard'))
    
    # Créer un fichier ZIP temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        zip_path = tmp_file.name
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isdir(treatment_path):
                # Ajouter tous les fichiers du traitement
                for root, dirs, files in os.walk(treatment_path):
                    # Calculer le chemin relatif depuis treatment_path
                    relative_root = os.path.relpath(root, treatment_path)
                    
                    # Ajouter tous les fichiers
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Créer le nom d'archive en préservant la structure des dossiers
                        if relative_root == '.':
                            # Fichier à la racine du traitement
                            archive_name = f"treatment_results/{file}"
                        else:
                            # Fichier dans un sous-dossier du traitement
                            archive_name = f"treatment_results/{os.path.join(relative_root, file).replace('\\', '/')}"
                        zipf.write(file_path, archive_name)
                
                # Ajouter les fichiers sources originaux si disponibles
                if projet and projet.emplacement_source:
                    # Construire le chemin absolu du dossier source
                    if os.path.isabs(projet.emplacement_source):
                        source_path = projet.emplacement_source
                    else:
                        current_dir = os.getcwd()
                        if current_dir.endswith('app'):
                            project_root = os.path.dirname(current_dir)
                        else:
                            project_root = current_dir
                        source_path = os.path.join(project_root, projet.emplacement_source)
                    
                    if os.path.exists(source_path) and os.path.isdir(source_path):
                        print(f"DEBUG: Adding specific original files from {source_path}")
                        
                        # Add only the specific original files (fichier_1 and fichier_2)
                        original_files = []
                        if projet.fichier_1:
                            original_files.append(projet.fichier_1)
                        if projet.fichier_2:
                            original_files.append(projet.fichier_2)
                        
                        for original_filename in original_files:
                            if original_filename:
                                # Clean filename (remove any path components)
                                clean_filename = os.path.basename(original_filename)
                                original_file_path = os.path.join(source_path, clean_filename)
                                
                                if os.path.exists(original_file_path) and os.path.isfile(original_file_path):
                                    archive_name = f"original_files/{clean_filename}"
                                    zipf.write(original_file_path, archive_name)
                                    print(f"DEBUG: Added original file {clean_filename} as {archive_name}")
                                else:
                                    print(f"DEBUG: Original file not found: {original_file_path}")
                    else:
                        print(f"DEBUG: Source path does not exist or is not a directory: {source_path}")
                        
            else:
                flash("Le chemin de traitement n'est pas un dossier valide", "error")
                return redirect(url_for('projets.dashboard'))
        
        # Nom du fichier ZIP avec le nom du traitement et la date
        treatment_name = treatment.nom_traitement_projet or f"Treatment_{treatment.id}"
        date_str = treatment.date_execution.strftime('%Y%m%d_%H%M%S') if treatment.date_execution else 'unknown'
        zip_filename = f"{treatment_name}_{date_str}.zip"
        
        return send_file(zip_path, 
                        as_attachment=True, 
                        download_name=zip_filename,
                        mimetype='application/zip')
    
    except Exception as e:
        flash(f"Erreur lors de la création du ZIP de traitement : {e}", "error")
        return redirect(url_for('projets.dashboard'))
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except:
                pass

@projets_bp.route('/download-report-file/<int:projet_id>/<filename>')
@login_required
def download_report_file(projet_id, filename):
    """Route pour télécharger un fichier de rapport spécifique"""
    projet = Projet.query.get_or_404(projet_id)
    
    # Vérifier les permissions : seul le propriétaire ou l'admin peut télécharger
    if not current_user.is_admin() and projet.user_id != current_user.id:
        flash("Accès non autorisé à ce projet", "error")
        return redirect(url_for('projets.dashboard'))
    
    if not projet.emplacement_archive:
        flash("Dossier d'archive introuvable", "error")
        return redirect(url_for('projets.dashboard'))
    
    # Construire le chemin absolu depuis la racine du projet
    if os.path.isabs(projet.emplacement_archive):
        archive_path = projet.emplacement_archive
    else:
        # Méthode plus robuste : partir du répertoire courant et remonter si nécessaire
        current_dir = os.getcwd()
        if current_dir.endswith('app'):
            # Si on est dans le dossier app/, remonter d'un niveau
            project_root = os.path.dirname(current_dir)
        else:
            # Sinon, on est déjà à la racine
            project_root = current_dir
        archive_path = os.path.join(project_root, projet.emplacement_archive)
    
    if not os.path.exists(archive_path):
        flash(f"Dossier d'archive introuvable: {archive_path}", "error")
        return redirect(url_for('projets.dashboard'))
    
    file_path = os.path.join(archive_path, filename)
    
    if not os.path.exists(file_path):
        flash(f"Fichier introuvable: {file_path}", "error")
        return redirect(url_for('projets.dashboard'))
    
    return send_file(file_path, as_attachment=True, download_name=filename)

@projets_bp.route('/download-treatment-file/<int:treatment_id>/<file_type>')
@login_required
def download_treatment_file(treatment_id, file_type):
    """Route pour télécharger un fichier spécifique d'un traitement (excel, pdf, chart)"""
    from app.models.fichier_genere import FichierGenere
    
    print(f"DEBUG DOWNLOAD: treatment_id={treatment_id}, file_type={file_type}")
    
    treatment = FichierGenere.query.get_or_404(treatment_id)
    print(f"DEBUG DOWNLOAD: Found treatment: {treatment.id}")
    print(f"DEBUG DOWNLOAD: chemin_archive={treatment.chemin_archive}")
    print(f"DEBUG DOWNLOAD: nom_fichier_excel={treatment.nom_fichier_excel}")
    print(f"DEBUG DOWNLOAD: nom_fichier_pdf={treatment.nom_fichier_pdf}")
    print(f"DEBUG DOWNLOAD: nom_fichier_graphe={treatment.nom_fichier_graphe}")
    
    # Vérifier les permissions via le projet parent
    projet = treatment.projet
    if projet and not current_user.is_admin() and projet.user_id != current_user.id:
        flash("Accès non autorisé à ce traitement", "error")
        return redirect(url_for('projets.dashboard'))
    
    if not treatment.chemin_archive:
        flash("Dossier de traitement introuvable", "error")
        print(f"DEBUG DOWNLOAD: ERROR - No chemin_archive")
        return redirect(url_for('projets.dashboard'))
    
    # Construire le chemin absolu du traitement
    # Dans un conteneur Docker, le chemin devrait être absolu depuis /app
    if os.path.isabs(treatment.chemin_archive):
        treatment_path = treatment.chemin_archive
    else:
        # Pour Docker, construire le chemin depuis /app
        current_dir = os.getcwd()
        print(f"DEBUG DOWNLOAD: current_dir={current_dir}")
        
        if '/app' in current_dir:
            # Nous sommes dans un conteneur Docker
            app_root = '/app'
            treatment_path = os.path.join(app_root, treatment.chemin_archive)
        else:
            # Développement local
            if current_dir.endswith('app'):
                project_root = os.path.dirname(current_dir)
            else:
                project_root = current_dir
            treatment_path = os.path.join(project_root, treatment.chemin_archive)
    
    print(f"DEBUG DOWNLOAD: treatment_path={treatment_path}")
    print(f"DEBUG DOWNLOAD: path exists? {os.path.exists(treatment_path)}")
    
    if not os.path.exists(treatment_path):
        # Essayer un chemin alternatif pour les traitements
        # Si chemin_archive ne contient pas "treatment_", chercher le sous-dossier treatment
        if 'treatment_' not in treatment_path:
            # Lister les dossiers pour trouver le dossier treatment_*
            try:
                if os.path.exists(treatment_path):
                    treatment_dirs = [d for d in os.listdir(treatment_path) if d.startswith('treatment_')]
                    if treatment_dirs:
                        treatment_path = os.path.join(treatment_path, treatment_dirs[0])
                        print(f"DEBUG DOWNLOAD: Trying treatment subdir: {treatment_path}")
            except Exception as e:
                print(f"DEBUG DOWNLOAD: Error listing directory: {e}")
        
        if not os.path.exists(treatment_path):
            flash(f"Dossier de traitement introuvable: {treatment_path}", "error")
            print(f"DEBUG DOWNLOAD: ERROR - Path doesn't exist: {treatment_path}")
            return redirect(url_for('projets.dashboard'))
    
    # Déterminer le fichier à télécharger selon le type
    file_path = None
    filename = None
    
    if file_type == 'excel' and treatment.nom_fichier_excel:
        # Handle both old format (just filename) and new format (path/filename)
        if '/' in treatment.nom_fichier_excel or '\\' in treatment.nom_fichier_excel:
            # New format: file path includes subdirectory, extract just the filename
            filename = os.path.basename(treatment.nom_fichier_excel)
            # Check if we need to look in a subdirectory
            file_subdir = os.path.dirname(treatment.nom_fichier_excel)
            if file_subdir:
                file_path = os.path.join(treatment_path, file_subdir, filename)
            else:
                file_path = os.path.join(treatment_path, filename)
        else:
            # Old format: just filename
            filename = treatment.nom_fichier_excel
            file_path = os.path.join(treatment_path, filename)
        print(f"DEBUG DOWNLOAD: Excel - filename={filename}, file_path={file_path}")
        
    elif file_type == 'pdf' and treatment.nom_fichier_pdf:
        # Handle both old format (just filename) and new format (path/filename)
        if '/' in treatment.nom_fichier_pdf or '\\' in treatment.nom_fichier_pdf:
            # New format: file path includes subdirectory, extract just the filename
            filename = os.path.basename(treatment.nom_fichier_pdf)
            # Check if we need to look in a subdirectory
            file_subdir = os.path.dirname(treatment.nom_fichier_pdf)
            if file_subdir:
                file_path = os.path.join(treatment_path, file_subdir, filename)
            else:
                file_path = os.path.join(treatment_path, filename)
        else:
            # Old format: just filename
            filename = treatment.nom_fichier_pdf
            file_path = os.path.join(treatment_path, filename)
        print(f"DEBUG DOWNLOAD: PDF - filename={filename}, file_path={file_path}")
        
    elif file_type == 'chart' and treatment.nom_fichier_graphe:
        # Handle both old format (just filename) and new format (path/filename)
        if '/' in treatment.nom_fichier_graphe or '\\' in treatment.nom_fichier_graphe:
            # New format: file path includes subdirectory, extract just the filename
            filename = os.path.basename(treatment.nom_fichier_graphe)
            # Check if we need to look in a subdirectory
            file_subdir = os.path.dirname(treatment.nom_fichier_graphe)
            if file_subdir:
                file_path = os.path.join(treatment_path, file_subdir, filename)
            else:
                file_path = os.path.join(treatment_path, filename)
        else:
            # Old format: just filename
            filename = treatment.nom_fichier_graphe
            file_path = os.path.join(treatment_path, filename)
        print(f"DEBUG DOWNLOAD: Chart - filename={filename}, file_path={file_path}")
    
    # If the file doesn't exist at the expected location, try alternative locations
    if file_path and not os.path.exists(file_path):
        print(f"DEBUG DOWNLOAD: File not found at {file_path}, trying alternatives...")
        
        # Try directly in the treatment directory
        alt_file_path = os.path.join(treatment_path, filename)
        if os.path.exists(alt_file_path):
            file_path = alt_file_path
            print(f"DEBUG DOWNLOAD: Found file at alternative location: {file_path}")
        else:
            # Try looking in the parent directory (project archive)
            if treatment.projet and treatment.projet.emplacement_archive:
                if '/app' in os.getcwd():
                    app_root = '/app'
                    parent_archive = os.path.join(app_root, treatment.projet.emplacement_archive)
                else:
                    parent_archive = treatment.projet.emplacement_archive
                
                parent_file_path = os.path.join(parent_archive, filename)
                if os.path.exists(parent_file_path):
                    file_path = parent_file_path
                    print(f"DEBUG DOWNLOAD: Found file in parent archive: {file_path}")
    
    if not file_path or not filename:
        flash(f"Fichier {file_type} non disponible pour ce traitement", "error")
        print(f"DEBUG DOWNLOAD: ERROR - No file_path or filename for type {file_type}")
        return redirect(url_for('projets.dashboard'))
    
    print(f"DEBUG DOWNLOAD: Final file_path={file_path}, exists? {os.path.exists(file_path)}")
    
    if not os.path.exists(file_path):
        flash(f"Fichier {file_type} introuvable: {file_path}", "error")
        print(f"DEBUG DOWNLOAD: ERROR - File doesn't exist: {file_path}")
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
    
    # Calculate stats for the template
    total_logs = LogExecution.query.count()
    success_logs = LogExecution.query.filter_by(statut='success').count()
    error_logs = LogExecution.query.filter_by(statut='error').count()
    warning_logs = LogExecution.query.filter_by(statut='warning').count()
    
    stats = {
        'total': total_logs,
        'success': success_logs,
        'error': error_logs,
        'warning': warning_logs
    }
    
    # Create current_filters for template
    current_filters = {
        'status': None,
        'log_type': log_type,
        'date_range': None
    }
    
    return render_template('all_logs.html', logs=logs, log_type=log_type, stats=stats, current_filters=current_filters)

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

@projets_bp.route('/request-treatment-deletion/<int:fichier_genere_id>', methods=['POST'])
@login_required
def request_treatment_deletion(fichier_genere_id):
    """Allow users to request treatment deletion from FichierGenere table"""
    fichier_genere = FichierGenere.query.get_or_404(fichier_genere_id)
    reason = request.form.get('reason', '')
    
    # Get the parent project for naming
    projet = Projet.query.get(fichier_genere.projet_id)
    treatment_name = fichier_genere.nom_traitement_projet or f"Treatment {fichier_genere.id}"
    
    # Check if user is admin (admin can delete directly)
    if current_user.is_admin():
        # Admin can delete directly
        try:
            # Delete associated files first
            file_deletion_result = delete_project_files(projet, fichier_genere)
            file_cleanup_summary = get_file_cleanup_summary(file_deletion_result)
            
            db.session.delete(fichier_genere)
            db.session.commit()
            flash(f'Treatment "{treatment_name}" has been deleted successfully. {file_cleanup_summary}', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting treatment. Please try again.', 'error')
    else:
        # Regular users must request deletion
        # Check if a deletion request already exists for this treatment
        existing_request = DeletionRequest.query.filter_by(
            fichier_genere_id=fichier_genere_id, 
            status='pending'
        ).first()
        
        if existing_request:
            flash('A deletion request for this treatment is already pending.', 'info')
        else:
            # Create new deletion request
            deletion_request = DeletionRequest(
                user_id=current_user.id,
                fichier_genere_id=fichier_genere_id,
                projet_id=fichier_genere.projet_id,  # Keep project reference for context
                reason=reason,
                status='pending'
            )
            
            try:
                db.session.add(deletion_request)
                db.session.commit()
                
                # Create notification for user
                create_notification(
                    user_id=current_user.id,
                    title="Treatment Deletion Request Submitted",
                    message=f"Your request to delete treatment '{treatment_name}' from project '{projet.nom_projet if projet else 'Unknown'}' has been submitted and is awaiting admin approval.",
                    notification_type='info',
                    related_request_id=deletion_request.id
                )
                
                # Notify all admins about the new deletion request
                notify_all_admins(
                    title="New Treatment Deletion Request",
                    message=f"User {current_user.username} has requested deletion of treatment '{treatment_name}' from project '{projet.nom_projet if projet else 'Unknown'}'. Please review the request.",
                    notification_type='warning',
                    related_request_id=deletion_request.id
                )
                
                flash('Treatment deletion request submitted successfully. An administrator will review it.', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error submitting deletion request. Please try again.', 'error')
    
    return redirect(url_for('projets.dashboard'))

@projets_bp.route('/request-deletion/<int:projet_id>', methods=['POST'])
@login_required
def request_deletion(projet_id):
    """Allow users to request project deletion (non-admin users)"""
    projet = Projet.query.get_or_404(projet_id)
    reason = request.form.get('reason', '')
    
    # Check if user is admin (admin can delete directly)
    if current_user.is_admin():
        # Admin can delete directly - preserve logs like in admin route
        try:
            # Delete associated files first
            file_deletion_result = delete_project_files(projet)
            file_cleanup_summary = get_file_cleanup_summary(file_deletion_result)
            
            # Update project logs to set projet_id to NULL (preserve logs)
            for log in projet.logs:
                log.projet_id = None
            
            # Delete the project (cascade will handle related records except logs)
            db.session.delete(projet)
            db.session.commit()
            flash(f'Project "{projet.nom_projet}" has been deleted successfully. {file_cleanup_summary}', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting project. Please try again.', 'error')
    else:
        # Regular users must request deletion
        # Check if a deletion request already exists for this project
        existing_request = DeletionRequest.query.filter_by(
            projet_id=projet_id, 
            status='pending'
        ).first()
        
        if existing_request:
            flash('A deletion request for this project is already pending.', 'info')
        else:
            # Create new deletion request
            deletion_request = DeletionRequest(
                user_id=current_user.id,
                projet_id=projet_id,
                reason=reason,
                status='pending'
            )
            
            try:
                db.session.add(deletion_request)
                db.session.commit()
                
                # Create notification for user
                create_notification(
                    user_id=current_user.id,
                    title="Deletion Request Submitted",
                    message=f"Your request to delete project '{projet.nom_projet}' has been submitted and is awaiting admin approval.",
                    notification_type='info',
                    related_request_id=deletion_request.id
                )
                
                # Notify all admins about the new deletion request
                notify_all_admins(
                    title="New Project Deletion Request",
                    message=f"User {current_user.username} has requested deletion of project '{projet.nom_projet}'. Please review the request.",
                    notification_type='warning',
                    related_request_id=deletion_request.id
                )
                
                flash('Deletion request submitted successfully. An administrator will review it.', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error submitting deletion request. Please try again.', 'error')
    
    return redirect(url_for('projets.dashboard'))

@projets_bp.route('/treatment-details/<int:treatment_id>')
@login_required
def treatment_details(treatment_id):
    """Route pour afficher les détails d'un traitement spécifique avec ses statistiques"""
    try:
        print(f"DEBUG: Début traitement treatment ID: {treatment_id}")
        
        # Récupérer le FichierGenere pour obtenir les informations du traitement
        fichier_genere = FichierGenere.query.get_or_404(treatment_id)
        projet = fichier_genere.projet
        
        # Vérifier les permissions : seul le propriétaire ou l'admin peut voir les détails
        if not current_user.is_admin() and projet.user_id != current_user.id:
            return jsonify({
                'error': True,
                'message': 'Accès non autorisé à ce traitement'
            }), 403
        
        print(f"DEBUG: Traitement trouvé - Excel: {fichier_genere.nom_fichier_excel}, PDF: {fichier_genere.nom_fichier_pdf}, Graphe: {fichier_genere.nom_fichier_graphe}")
        
        # Récupérer les statistiques spécifiques à ce traitement par date d'exécution
        try:
            # D'abord essayer de trouver les statistiques avec la date exacte
            stats = StatistiqueEcart.query.filter_by(
                projet_id=projet.id,
                date_execution=fichier_genere.date_execution
            ).first()
            print(f"DEBUG: Statistiques pour la date exacte {fichier_genere.date_execution}: {stats is not None}")
            
            # Si pas trouvé, chercher dans une plage de temps autour de la date d'exécution (±1 heure)
            if not stats:
                from datetime import timedelta
                date_min = fichier_genere.date_execution - timedelta(hours=1)
                date_max = fichier_genere.date_execution + timedelta(hours=1)
                
                stats = StatistiqueEcart.query.filter(
                    StatistiqueEcart.projet_id == projet.id,
                    StatistiqueEcart.date_execution >= date_min,
                    StatistiqueEcart.date_execution <= date_max
                ).order_by(StatistiqueEcart.date_execution.desc()).first()
                print(f"DEBUG: Statistiques dans la plage {date_min} - {date_max}: {stats is not None}")
            
            # Si toujours pas trouvé, prendre la plus récente du projet
            if not stats:
                stats = StatistiqueEcart.query.filter_by(projet_id=projet.id).order_by(
                    StatistiqueEcart.date_execution.desc()
                ).first()
                print(f"DEBUG: Utilisation des statistiques les plus récentes: {stats is not None}")
                
        except Exception as e:
            print(f"ERREUR lors de la récupération des statistiques: {e}")
            stats = None
        
        # Construire les chemins pour vérifier l'existence des fichiers
        rapport_excel_path = None
        rapport_pdf_path = None
        chart_path = None
        has_files_to_download = False
        
        # Vérifier l'existence des fichiers dans l'archive
        if fichier_genere.chemin_archive or projet.emplacement_archive:
            # Utiliser le chemin du fichier généré ou celui du projet
            archive_path = fichier_genere.chemin_archive or projet.emplacement_archive
            
            if not os.path.isabs(archive_path):
                current_dir = os.getcwd()
                if '/app' in current_dir:
                    app_root = '/app'
                    archive_path = os.path.join(app_root, archive_path)
                else:
                    if current_dir.endswith('app'):
                        project_root = os.path.dirname(current_dir)
                    else:
                        project_root = current_dir
                    archive_path = os.path.join(project_root, archive_path)
            
            print(f"DEBUG: Chemin d'archive: {archive_path}")
            print(f"DEBUG: Archive existe: {os.path.exists(archive_path)}")
            
            if archive_path and os.path.exists(archive_path):
                print(f"DEBUG: Contenu de l'archive: {os.listdir(archive_path) if os.path.exists(archive_path) else 'Non accessible'}")
                
                # Vérifier les fichiers spécifiques du traitement
                if fichier_genere.nom_fichier_excel:
                    excel_path = os.path.join(archive_path, fichier_genere.nom_fichier_excel)
                    if os.path.exists(excel_path):
                        rapport_excel_path = excel_path
                        print(f"DEBUG: Fichier Excel trouvé: {excel_path}")
                
                if fichier_genere.nom_fichier_pdf:
                    pdf_path = os.path.join(archive_path, fichier_genere.nom_fichier_pdf)
                    if os.path.exists(pdf_path):
                        rapport_pdf_path = pdf_path
                        print(f"DEBUG: Fichier PDF trouvé: {pdf_path}")
                
                if fichier_genere.nom_fichier_graphe:
                    chart_path_file = os.path.join(archive_path, fichier_genere.nom_fichier_graphe)
                    if os.path.exists(chart_path_file):
                        chart_path = chart_path_file
                        print(f"DEBUG: Fichier graphique trouvé: {chart_path_file}")
                
                # Si pas de fichiers spécifiques, chercher directement dans le répertoire courant
                if not (rapport_excel_path or rapport_pdf_path or chart_path):
                    print(f"DEBUG: Recherche directe de fichiers dans {archive_path}")
                    try:
                        files_in_archive = os.listdir(archive_path)
                        print(f"DEBUG: Fichiers trouvés: {files_in_archive}")
                        
                        for file in files_in_archive:
                            file_path = os.path.join(archive_path, file)
                            if os.path.isfile(file_path):
                                if file.endswith('.xlsx') and not rapport_excel_path:
                                    rapport_excel_path = file_path
                                    print(f"DEBUG: Excel trouvé directement: {file_path}")
                                elif file.endswith('.pdf') and not rapport_pdf_path:
                                    rapport_pdf_path = file_path
                                    print(f"DEBUG: PDF trouvé directement: {file_path}")
                                elif file.endswith('.png') and not chart_path:
                                    chart_path = file_path
                                    print(f"DEBUG: Graphique trouvé directement: {file_path}")
                    except Exception as e:
                        print(f"DEBUG: Erreur lors de la lecture directe des fichiers: {e}")
                
                # Si toujours pas trouvé, chercher dans les sous-dossiers treatment_*
                if not (rapport_excel_path or rapport_pdf_path or chart_path):
                    print(f"DEBUG: Recherche de fichiers dans les sous-dossiers de {archive_path}")
                    
                    # Chercher récursivement dans l'archive pour trouver les dossiers treatment_
                    def find_treatment_directories(base_path, max_depth=3, current_depth=0):
                        """Recherche récursive des dossiers treatment_"""
                        found_dirs = []
                        if current_depth >= max_depth:
                            return found_dirs
                            
                        try:
                            for item in os.listdir(base_path):
                                item_path = os.path.join(base_path, item)
                                if os.path.isdir(item_path):
                                    if item.startswith('treatment_'):
                                        found_dirs.append(item_path)
                                        print(f"DEBUG: Dossier treatment trouvé: {item_path}")
                                    else:
                                        # Recherche récursive dans les sous-dossiers
                                        found_dirs.extend(find_treatment_directories(item_path, max_depth, current_depth + 1))
                        except Exception as e:
                            print(f"DEBUG: Erreur lors de la lecture du dossier {base_path}: {e}")
                        
                        return found_dirs
                    
                    treatment_dirs = find_treatment_directories(archive_path)
                    print(f"DEBUG: {len(treatment_dirs)} dossiers treatment trouvés")
                    
                    if treatment_dirs:
                        # Chercher le dossier correspondant à la date du traitement
                        treatment_date_str = fichier_genere.date_execution.strftime('%Y%m%d_%H%M%S')
                        print(f"DEBUG: Recherche de dossier correspondant à {treatment_date_str}")
                        
                        matching_dir = None
                        
                        for treatment_dir in treatment_dirs:
                            dir_name = os.path.basename(treatment_dir)
                            if treatment_date_str in dir_name:
                                matching_dir = treatment_dir
                                print(f"DEBUG: Correspondance exacte trouvée: {matching_dir}")
                                break
                        
                        # Si pas de correspondance exacte, prendre le plus récent
                        if not matching_dir:
                            matching_dir = sorted(treatment_dirs)[-1]
                            print(f"DEBUG: Aucune correspondance exacte, utilisation du plus récent: {matching_dir}")
                        
                        treatment_path = matching_dir
                        
                        # Vérifier l'existence des fichiers spécifiques
                        try:
                            files_found = os.listdir(treatment_path)
                            print(f"DEBUG: Fichiers dans {treatment_path}: {files_found}")
                            
                            for file in files_found:
                                if file.endswith('.xlsx'):
                                    rapport_excel_path = os.path.join(treatment_path, file)
                                    print(f"DEBUG: Excel trouvé: {rapport_excel_path}")
                                elif file.endswith('.pdf'):
                                    rapport_pdf_path = os.path.join(treatment_path, file)
                                    print(f"DEBUG: PDF trouvé: {rapport_pdf_path}")
                                elif file.endswith('.png'):
                                    chart_path = os.path.join(treatment_path, file)
                                    print(f"DEBUG: Graphique trouvé: {chart_path}")
                        except Exception as e:
                            print(f"DEBUG: Erreur lors de la lecture du dossier treatment {treatment_path}: {e}")
                    else:
                        print(f"DEBUG: Aucun dossier treatment_ trouvé dans {archive_path}")
            else:
                print(f"DEBUG: Chemin d'archive non valide ou inexistant: {archive_path}")
        
        print(f"DEBUG: Résultat final - Excel: {rapport_excel_path is not None}, PDF: {rapport_pdf_path is not None}, Chart: {chart_path is not None}")
        has_files_to_download = bool(rapport_excel_path or rapport_pdf_path or chart_path)
        
        # Compiler les statistiques de manière défensive
        fichier1_unique = 0
        fichier2_unique = 0
        communs = 0
        total_ecarts = 0
        date_execution = "N/A"
        
        if stats:
            try:
                fichier1_unique = getattr(stats, 'nb_ecarts_uniquement_fichier1', 0) or 0
                fichier2_unique = getattr(stats, 'nb_ecarts_uniquement_fichier2', 0) or 0
                communs = getattr(stats, 'nb_ecarts_communs', 0) or 0
                total_ecarts = fichier1_unique + fichier2_unique
                date_execution = stats.date_execution.strftime('%Y-%m-%d %H:%M:%S') if stats.date_execution else "N/A"
                print(f"DEBUG: Stats compilées - F1: {fichier1_unique}, F2: {fichier2_unique}, Communs: {communs}, Total: {total_ecarts}")
            except Exception as e:
                print(f"ERREUR lors de la compilation des stats: {e}")
        else:
            print(f"DEBUG: Aucune statistique trouvée pour le traitement {treatment_id}")
        
        # Compiler les informations du traitement
        try:
            treatment_info = {
                'id': projet.id,
                'treatment_id': treatment_id,
                'nom_projet': str(projet.nom_projet) if projet.nom_projet else "Nom non défini",
                'date_creation': projet.date_creation.strftime('%Y-%m-%d') if projet.date_creation else "Date non définie",
                'fichier_1': str(projet.fichier_1) if projet.fichier_1 else "Fichier 1 non défini",
                'fichier_2': str(projet.fichier_2) if projet.fichier_2 else "Fichier 2 non défini",
                'emplacement_archive': str(fichier_genere.chemin_archive or projet.emplacement_archive) if (fichier_genere.chemin_archive or projet.emplacement_archive) else "Non défini",
                'has_excel': bool(rapport_excel_path is not None),
                'has_pdf': bool(rapport_pdf_path is not None),
                'has_chart': bool(chart_path is not None),
                'has_files_to_download': bool(rapport_excel_path or rapport_pdf_path or chart_path),
                'statistics': {
                    'fichier1_unique': int(fichier1_unique),
                    'fichier2_unique': int(fichier2_unique),
                    'communs': int(communs),
                    'total_ecarts': int(total_ecarts),
                    'date_execution': str(date_execution)
                }
            }
            print(f"DEBUG: treatment_info créé avec succès pour traitement {treatment_id}")
        except Exception as e:
            print(f"ERREUR lors de la création de treatment_info: {e}")
            raise
        
        return jsonify(treatment_info)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERREUR COMPLÈTE dans treatment_details pour traitement {treatment_id}:")
        print(error_details)
        
        return jsonify({
            'error': True,
            'message': f"Erreur lors du chargement des détails du traitement: {str(e)}",
            'details': str(e)
        }), 500
