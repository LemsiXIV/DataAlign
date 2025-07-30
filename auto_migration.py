import os
import subprocess
import sys
from datetime import datetime

def init_auto_migration(app):
    """
    Génère automatiquement les migrations si nécessaire et les applique,
    uniquement si la config AUTO_MIGRATION est True.
    """
    if not app.config.get("AUTO_MIGRATION", False):
        print("⛔ Auto migration désactivée par configuration")
        return
    
    # Import des modèles dans le contexte de l'application
    with app.app_context():
        from app import db
        from app.models.logs import LogExecution
        
        def log_migration_action(statut, message, details=None):
            """Enregistre une action de migration dans les logs"""
            try:
                log_entry = LogExecution(
                    projet_id=None,  # Migration automatique, pas liée à un projet spécifique
                    statut=statut,
                    message=f"Migration automatique: {message}",
                    details=details
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                print(f"❌ Erreur lors de l'enregistrement du log: {e}")
        
        MIGRATIONS_DIR = os.path.join(app.root_path, 'migrations')
        python_exec = sys.executable  # Python de l'environnement virtuel

        # Init si dossier migrations absent ou vide
        if not os.path.exists(MIGRATIONS_DIR) or not os.listdir(MIGRATIONS_DIR):
            print("📁 Dossier migrations introuvable ou vide, initialisation...")
            log_migration_action('info', 'Initialisation du dossier migrations')
            try:
                subprocess.run([python_exec, "cli.py", "db", "init"], check=True)
                log_migration_action('succès', 'Dossier migrations initialisé avec succès')
            except subprocess.CalledProcessError as e:
                error_msg = f"db init échoué (peut-être déjà initialisé) : {e}"
                print(f"⚠️ {error_msg}")
                log_migration_action('avertissement', error_msg)
        else:
            print("✅ Dossier migrations détecté")
            log_migration_action('info', 'Dossier migrations détecté')

        print("🔍 Vérification des changements de modèles...")
        log_migration_action('info', 'Début de la vérification des changements de modèles')

        result = subprocess.run(
            [python_exec, "cli.py", "db", "migrate", "-m", "Auto migration"],
            capture_output=True,
            text=True
        )

        if "No changes in schema detected" in result.stdout:
            print("✅ Aucun changement détecté dans les modèles")
            log_migration_action('info', 'Aucun changement détecté dans les modèles')
        else:
            print("✏️ Fichier de migration généré")
            log_migration_action('succès', 'Fichier de migration généré', details=result.stdout)

        print("⬆️ Application des migrations...")
        log_migration_action('info', 'Début de l\'application des migrations')
        try:
            upgrade_result = subprocess.run([python_exec, "cli.py", "db", "upgrade"], 
                                          capture_output=True, text=True, check=True)
            log_migration_action('succès', 'Migrations appliquées avec succès', details=upgrade_result.stdout)
        except subprocess.CalledProcessError as e:
            error_msg = f"Erreur lors de l'application des migrations : {e}"
            print(f"❌ {error_msg}")
            log_migration_action('échec', error_msg, details=str(e))

        print("✅ Base de données à jour")
        log_migration_action('succès', 'Base de données mise à jour avec succès')