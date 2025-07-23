#!/usr/bin/env python3
"""Script de debug pour vérifier les projets dans la base de données"""

from app import create_app, db
from app.models import Projet
from collections import defaultdict

def debug_projets():
    app = create_app()
    with app.app_context():
        # Récupérer tous les projets
        projets = Projet.query.order_by(Projet.nom_projet, Projet.date_creation.desc()).all()
        
        print("=== TOUS LES PROJETS ===")
        for projet in projets:
            print(f"ID: {projet.id}")
            print(f"  Nom: {projet.nom_projet}")
            print(f"  Date: {projet.date_creation}")
            print(f"  Fichier 1: {projet.fichier_1}")
            print(f"  Fichier 2: {projet.fichier_2}")
            print(f"  Archive: {projet.emplacement_archive}")
            print("-" * 50)
        
        # Organiser par nom de projet
        projets_tree = defaultdict(list)
        for projet in projets:
            formatted_date_with_time = projet.date_creation.strftime("%d/%m/%Y à %H:%M") if projet.date_creation else "N/A"
            
            projets_tree[projet.nom_projet].append({
                'id': projet.id,
                'date_creation': projet.date_creation,
                'fichier_1': projet.fichier_1,
                'fichier_2': projet.fichier_2,
                'emplacement_archive': projet.emplacement_archive,
                'formatted_date': formatted_date_with_time
            })
        
        print("\n=== ARBORESCENCE ===")
        for nom_projet, traitements in projets_tree.items():
            print(f"Projet: {nom_projet} - {len(traitements)} traitement(s)")
            for i, traitement in enumerate(traitements, 1):
                print(f"  {i}. ID: {traitement['id']}")
                print(f"     Date: {traitement['formatted_date']}")
                print(f"     Fichiers: {traitement['fichier_1']} | {traitement['fichier_2']}")
                print(f"     Archive: {traitement['emplacement_archive']}")
                print()

if __name__ == "__main__":
    debug_projets()
