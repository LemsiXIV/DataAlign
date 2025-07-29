#!/usr/bin/env python3
"""
Debug des chemins dans l'environnement Flask
"""
from app import create_app
import os

def debug_paths():
    """Debug des chemins Flask"""
    app = create_app()
    
    with app.app_context():
        # Simuler exactement ce qui se fait dans les routes
        current_file = __file__
        print(f"🔍 Script actuel: {current_file}")
        
        # Simuler le chemin de projets.py
        projets_file = os.path.join(os.path.dirname(current_file), 'app', 'routes', 'projets.py')
        print(f"📁 Projets.py simulé: {projets_file}")
        
        # Test avec 3 dirname
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(projets_file)))
        print(f"🏠 Project root (3 dirname): {project_root}")
        
        # Test chemin d'archive
        test_archive = "uploads/archive/first_test_20250729_105021"
        archive_path = os.path.join(project_root, test_archive)
        print(f"📦 Chemin archive: {archive_path}")
        print(f"✅ Archive existe: {os.path.exists(archive_path)}")
        
        if os.path.exists(archive_path):
            excel_path = os.path.join(archive_path, "rapport_comparaison.xlsx")
            print(f"📊 Excel path: {excel_path}")
            print(f"✅ Excel existe: {os.path.exists(excel_path)}")

if __name__ == "__main__":
    debug_paths()
