from app import create_app, db
from app.models.logs import LogExecution
from auto_migration import init_auto_migration
import os
import time
import threading
from datetime import datetime
import sys
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


def wait_for_database(app, max_retries=30, retry_interval=2):
    """
    Attend que la base de données soit disponible
    """
    print(f"🔌 Vérification de la connexion à la base de données...")
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                # Test simple de connexion
                db.session.execute(text('SELECT 1'))
                print(f"✅ Connexion à la base de données établie (tentative {attempt + 1})")
                return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                print(f"⏳ Tentative {attempt + 1}/{max_retries} échouée: {str(e)[:100]}...")
                print(f"   Nouvelle tentative dans {retry_interval} secondes...")
                time.sleep(retry_interval)
            else:
                print(f"❌ Impossible de se connecter à la base de données après {max_retries} tentatives")
                print(f"   Dernière erreur: {e}")
                return False
        except Exception as e:
            print(f"❌ Erreur inattendue lors de la connexion à la DB: {e}")
            return False
    
    return False

def cleanup_temp_files():
    """
    Supprime les fichiers temporaires plus anciens que 5 heures
    et enregistre les actions dans la table logs
    """
    TEMP_DIR = "temp"
    MAX_AGE_HOURS = 5
    
    # Use the global app instance instead of creating a new one
    with app.app_context():
        # Check if logs_execution table exists before trying to log
        def safe_log(message, statut='succès'):
            try:
                log_entry = LogExecution(
                    projet_id=None,
                    statut=statut,
                    message=message
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                # If logging fails, just print to console
                print(f"[{datetime.now()}] Impossible d'enregistrer dans les logs: {e}")
                print(f"[{datetime.now()}] Message: {message}")
        if not os.path.exists(TEMP_DIR):
            # Enregistrer dans les logs que le dossier n'existe pas
            safe_log(f"Nettoyage automatique: Le dossier {TEMP_DIR} n'existe pas", 'échec')
            print(f"[{datetime.now()}] Le dossier {TEMP_DIR} n'existe pas")
            return
        
        current_time = time.time()
        cutoff_time = current_time - (MAX_AGE_HOURS * 3600)
        
        deleted_count = 0
        deleted_files = []
        errors = []
        
        try:
            for filename in os.listdir(TEMP_DIR):
                file_path = os.path.join(TEMP_DIR, filename)
                
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_time:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            age_hours = (current_time - file_mtime) / 3600
                            
                            deleted_files.append({
                                'filename': filename,
                                'age_hours': age_hours,
                                'size': file_size
                            })
                            
                            print(f"[{datetime.now()}] Supprimé: {filename} (âge: {age_hours:.1f}h, taille: {file_size} bytes)")
                        except OSError as e:
                            error_msg = f"Erreur lors de la suppression de {filename}: {e}"
                            errors.append(error_msg)
                            print(f"[{datetime.now()}] {error_msg}")
        
        except OSError as e:
            error_msg = f"Erreur lors de l'accès au dossier {TEMP_DIR}: {e}"
            
            # Enregistrer l'erreur dans les logs
            safe_log(f"Nettoyage automatique: {error_msg}", 'échec')
            
            print(f"[{datetime.now()}] {error_msg}")
            return
        
        # Enregistrer le résultat du nettoyage dans les logs
        if deleted_count > 0 or errors:
            total_size = sum(f['size'] for f in deleted_files)
            size_mb = total_size / (1024 * 1024)
            
            # Créer le message de résumé
            summary_parts = []
            if deleted_count > 0:
                summary_parts.append(f"{deleted_count} fichiers supprimés ({size_mb:.2f} MB)")
                
                # Détail des fichiers supprimés
                files_detail = []
                for f in deleted_files:
                    files_detail.append(f"- {f['filename']} (âge: {f['age_hours']:.1f}h, {f['size']} bytes)")
                
                if files_detail:
                    summary_parts.append("Fichiers supprimés:\n" + "\n".join(files_detail))
            
            if errors:
                summary_parts.append(f"{len(errors)} erreurs rencontrées:\n" + "\n".join(errors))
            
            message = "Nettoyage automatique des fichiers temporaires:\n" + "\n".join(summary_parts)
            
            statut = 'succès' if not errors else ('échec' if deleted_count == 0 else 'succès')
            
            safe_log(message, statut)
            
            print(f"[{datetime.now()}] Nettoyage terminé: {deleted_count} fichiers supprimés, {size_mb:.2f} MB libérés")
        else:
            # Aucun fichier à supprimer
            safe_log("Nettoyage automatique: Aucun fichier temporaire à supprimer", 'succès')
            
            print(f"[{datetime.now()}] Aucun fichier à supprimer")

def start_cleanup_timer():
    """
    Démarre un timer pour le nettoyage automatique toutes les 5 heures
    """
    # Wait a bit to ensure database is fully initialized
    time.sleep(5)
    
    cleanup_temp_files()  # Nettoyage initial
    
    # Programmer le prochain nettoyage dans 5 heures (18000 secondes)
    timer = threading.Timer(18000, start_cleanup_timer)
    timer.daemon = True
    timer.start()
    
    print(f"[{datetime.now()}] Prochain nettoyage programmé dans 5 heures")

def initialize_app():
    """
    Initialize the application - runs both for direct execution and Gunicorn
    """
    env = os.getenv('FLASK_ENV', 'development')
    print(f"🌍 Environnement: {env}")
    print("🏗️ Initialisation de l'application Flask...")

    # 1. Attendre que la base de données soit prête
    if not wait_for_database(app):
        print("❌ Impossible de se connecter à la base de données. Arrêt de l'application.")
        if __name__ == '__main__':
            sys.exit(1)
        else:
            # For Gunicorn, we can't exit, but we can raise an exception
            raise RuntimeError("Database connection failed")

    with app.app_context():
        print("🔄 Initialisation des migrations automatiques...")
        try:
            init_auto_migration(app)
            print("✅ Migrations automatiques terminées")
        except Exception as e:
            print(f"❌ Erreur lors des migrations automatiques: {e}")
            print("⚠️ L'application va continuer mais certaines fonctionnalités peuvent ne pas fonctionner")

        # Retry table creation with better error handling
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.create_all()
                print("✅ Tables de base de données vérifiées")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⏳ Tentative {attempt + 1} de création des tables échouée: {e}")
                    print("   Nouvelle tentative dans 2 secondes...")
                    time.sleep(2)
                else:
                    print(f"❌ Erreur lors de la création des tables après {max_retries} tentatives: {e}")

    # Only start cleanup timer after successful database initialization
    print(f"🧹 Démarrage du service de nettoyage automatique")
    start_cleanup_timer()

# Create the app globally so Gunicorn can import it
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

# Initialize the app - this runs both for direct execution and when imported by Gunicorn
initialize_app()

if __name__ == '__main__':
    print("🚀 Démarrage de l'application DataAlign en mode développement...")
    print(f"📍 L'application sera accessible sur http://localhost:5000")

    host = '0.0.0.0'  
    port = int(os.environ.get('PORT', 5000))
    debug = (env == 'development')
    
    app.run(host=host, port=port, debug=debug)