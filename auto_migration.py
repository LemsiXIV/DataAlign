import os
import subprocess
import sys

def init_auto_migration(app):
    """
    Génère automatiquement les migrations si nécessaire et les applique,
    uniquement si la config AUTO_MIGRATION est True.
    """
    if not app.config.get("AUTO_MIGRATION", False):
        print("⛔ Auto migration désactivée par configuration")
        return
    
    MIGRATIONS_DIR = os.path.join(app.root_path, 'migrations')
    python_exec = sys.executable  # Python de l'environnement virtuel

    # Init si dossier migrations absent ou vide
    if not os.path.exists(MIGRATIONS_DIR) or not os.listdir(MIGRATIONS_DIR):
        print("📁 Dossier migrations introuvable ou vide, initialisation...")
        try:
            subprocess.run([python_exec, "cli.py", "db", "init"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ db init échoué (peut-être déjà initialisé) : {e}")
    else:
        print("✅ Dossier migrations détecté")

    print("🔍 Vérification des changements de modèles...")

    result = subprocess.run(
        [python_exec, "cli.py", "db", "migrate", "-m", "Auto migration"],
        capture_output=True,
        text=True
    )

    if "No changes in schema detected" in result.stdout:
        print("✅ Aucun changement détecté dans les modèles")
    else:
        print("✏️ Fichier de migration généré")

    print("⬆️ Application des migrations...")
    try:
        subprocess.run([python_exec, "cli.py", "db", "upgrade"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'application des migrations : {e}")

    print("✅ Base de données à jour")
