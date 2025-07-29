#!/usr/bin/env python3
"""
Test rapide des corrections de chemins
"""
import os

# Simuler la logique de correction
print("🔍 Test de la logique de correction des chemins:")

# Simuler __file__ comme si on était dans app/routes/projets.py
current_file = os.path.join(os.getcwd(), 'app', 'routes', 'projets.py')
print(f"Fichier courant simulé: {current_file}")

# Calcul du project_root
project_root = os.path.dirname(os.path.dirname(current_file))
print(f"Racine du projet: {project_root}")

# Test avec un chemin relatif
relative_path = "uploads/archive/first_test_20250729_105021"
archive_path = os.path.join(project_root, relative_path)
print(f"Chemin d'archive calculé: {archive_path}")
print(f"Archive existe: {'✅' if os.path.exists(archive_path) else '❌'}")

if os.path.exists(archive_path):
    # Test des fichiers spécifiques
    excel_path = os.path.join(archive_path, "rapport_comparaison.xlsx")
    pdf_path = os.path.join(archive_path, "rapport_comparaison.pdf")
    
    print(f"Excel existe: {'✅' if os.path.exists(excel_path) else '❌'}")
    print(f"PDF existe: {'✅' if os.path.exists(pdf_path) else '❌'}")
    
    print(f"\n📁 Contenu du dossier:")
    for file in os.listdir(archive_path):
        print(f"  - {file}")
