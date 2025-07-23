import os

folders = [
    "app",
    "app/models",
    "app/routes",
    "app/services",
    "app/templates",
    "app/static",
    "migrations"
]

files = {
    "run.py": "",
    "requirements.txt": "",
    "README.md": "# DataAlign - Automatisation DRC",
    "app/__init__.py": "",
    "app/config.py": "# Configuration Flask et base de données",
    "app/models/__init__.py": "",
    "app/models/projet.py": "",
    "app/models/fichier_genere.py": "",
    "app/models/statistiques.py": "",
    "app/models/configurations.py": "",
    "app/models/logs.py": "",
    "app/routes/__init__.py": "",
    "app/routes/projets.py": "",
    "app/routes/comparaison.py": "",
    "app/routes/fichiers.py": "",
    "app/routes/api.py": "",
    "app/services/__init__.py": "",
    "app/services/lecteur_fichier.py": "",
    "app/services/comparateur.py": "",
    "app/services/generateur_excel.py": "",
    "app/services/generateur_pdf.py": "",
}

for folder in folders:
    os.makedirs(folder, exist_ok=True)

for file_path, content in files.items():
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Structure Flask générée avec succès.")
