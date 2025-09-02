#!/usr/bin/env python3
"""
Script de debug pour analyser les problèmes de chemins
"""
import os
import sys

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.fichier_genere import FichierGenere
from app.models import Projet

def debug_paths():
    app = create_app()
    
    with app.app_context():
        print("=== DEBUG DES CHEMINS ===")
        print(f"Répertoire de travail actuel: {os.getcwd()}")
        
        # Lister tous les projets et leurs chemins
        projets = Projet.query.all()
        print(f"\n=== PROJETS ({len(projets)} trouvés) ===")
        
        for projet in projets:
            print(f"\nProjet ID: {projet.id}")
            print(f"  Nom: {projet.nom_projet}")
            print(f"  Emplacement archive: {projet.emplacement_archive}")
            
            if projet.emplacement_archive:
                abs_path = os.path.join('/app', projet.emplacement_archive) if projet.emplacement_archive.startswith('uploads/') else projet.emplacement_archive
                print(f"  Chemin absolu: {abs_path}")
                print(f"  Existe: {os.path.exists(abs_path)}")
                
                if os.path.exists(abs_path):
                    try:
                        files = os.listdir(abs_path)
                        print(f"  Fichiers: {files[:10]}...")  # Limiter l'affichage
                    except Exception as e:
                        print(f"  Erreur lors de la lecture: {e}")
        
        # Lister tous les fichiers générés
        fichiers = FichierGenere.query.all()
        print(f"\n=== FICHIERS GENERÉS ({len(fichiers)} trouvés) ===")
        
        for fichier in fichiers:
            print(f"\nFichier ID: {fichier.id}")
            print(f"  Projet ID: {fichier.projet_id}")
            print(f"  Nom traitement: {fichier.nom_traitement_projet}")
            print(f"  Chemin archive: {fichier.chemin_archive}")
            print(f"  Fichier graphe: {fichier.nom_fichier_graphe}")
            
            if fichier.chemin_archive:
                abs_path = os.path.join('/app', fichier.chemin_archive) if fichier.chemin_archive.startswith('uploads/') else fichier.chemin_archive
                print(f"  Chemin absolu: {abs_path}")
                print(f"  Existe: {os.path.exists(abs_path)}")
                
                if os.path.exists(abs_path):
                    try:
                        files = os.listdir(abs_path)
                        print(f"  Fichiers: {files}")
                        
                        # Vérifier spécifiquement le graphique
                        if fichier.nom_fichier_graphe:
                            chart_filename = os.path.basename(fichier.nom_fichier_graphe)
                            chart_path = os.path.join(abs_path, chart_filename)
                            print(f"  Graphique attendu: {chart_path}")
                            print(f"  Graphique existe: {os.path.exists(chart_path)}")
                    except Exception as e:
                        print(f"  Erreur lors de la lecture: {e}")

if __name__ == "__main__":
    debug_paths()
