from app import create_app, db
from app.models.logs import LogExecution
from auto_migration import init_auto_migration
import os
import time
import threading
from datetime import datetime

def cleanup_temp_files():
    """
    Supprime les fichiers temporaires plus anciens que 5 heures
    et enregistre les actions dans la table logs
    """
    TEMP_DIR = "temp"
    MAX_AGE_HOURS = 5
    
    # Créer le contexte de l'application pour accéder à la DB
    app = create_app()
    
    with app.app_context():
        if not os.path.exists(TEMP_DIR):
            # Enregistrer dans les logs que le dossier n'existe pas
            log_entry = LogExecution(
                projet_id=None,  # Pas de projet spécifique
                statut='échec',
                message=f"Nettoyage automatique: Le dossier {TEMP_DIR} n'existe pas"
            )
            db.session.add(log_entry)
            db.session.commit()
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
            log_entry = LogExecution(
                projet_id=None,
                statut='échec',
                message=f"Nettoyage automatique: {error_msg}"
            )
            db.session.add(log_entry)
            db.session.commit()
            
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
            
            log_entry = LogExecution(
                projet_id=None,
                statut=statut,
                message=message
            )
            db.session.add(log_entry)
            db.session.commit()
            
            print(f"[{datetime.now()}] Nettoyage terminé: {deleted_count} fichiers supprimés, {size_mb:.2f} MB libérés")
        else:
            # Aucun fichier à supprimer
            log_entry = LogExecution(
                projet_id=None,
                statut='succès',
                message="Nettoyage automatique: Aucun fichier temporaire à supprimer"
            )
            db.session.add(log_entry)
            db.session.commit()
            
            print(f"[{datetime.now()}] Aucun fichier à supprimer")

def start_cleanup_timer():
    """
    Démarre un timer pour le nettoyage automatique toutes les 5 heures
    """
    cleanup_temp_files()  # Nettoyage initial
    
    # Programmer le prochain nettoyage dans 5 heures (18000 secondes)
    timer = threading.Timer(18000, start_cleanup_timer)
    timer.daemon = True
    timer.start()
    
    print(f"[{datetime.now()}] Prochain nettoyage programmé dans 5 heures")

# Create Flask app using the app factory
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # 1. Exécuter les migrations automatiques en premier
        print("🔄 Initialisation des migrations automatiques...")
        try:
            init_auto_migration(app)
            print("✅ Migrations automatiques terminées")
        except Exception as e:
            print(f"❌ Erreur lors des migrations automatiques: {e}")
            print("⚠️ L'application va continuer mais certaines fonctionnalités peuvent ne pas fonctionner")
        
        # 2. Créer les tables si nécessaire (fallback)
        try:
            db.create_all()
            print("✅ Tables de base de données vérifiées")
        except Exception as e:
            print(f"❌ Erreur lors de la création des tables: {e}")
    
    # 3. Démarrer le service de nettoyage automatique
    print(f"🧹 Démarrage du service de nettoyage automatique")
    start_cleanup_timer()
    
    # 4. Démarrer l'application Flask
    print("🚀 Démarrage de l'application DataAlign...")
    app.run(debug=True)

