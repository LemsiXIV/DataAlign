#!/usr/bin/env python3
"""
Script pour tester spécifiquement le projet ID 3
"""
from app import create_app
from app.models import Projet
from app.models.statistiques import StatistiqueEcart
import json

def test_projet_3():
    """Tester spécifiquement le projet ID 3"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Test spécifique du projet ID 3")
            
            # Vérifier si le projet 3 existe
            projet = Projet.query.get(3)
            if not projet:
                print("❌ Projet ID 3 n'existe pas dans la base de données")
                
                # Lister tous les projets disponibles
                tous_projets = Projet.query.all()
                print(f"📋 Projets disponibles:")
                for p in tous_projets:
                    print(f"  - ID: {p.id}, Nom: {p.nom_projet}")
                return
            
            print(f"✅ Projet trouvé: {projet.nom_projet}")
            print(f"   Date création: {projet.date_creation}")
            print(f"   Fichier 1: {projet.fichier_1}")
            print(f"   Fichier 2: {projet.fichier_2}")
            print(f"   Archive: {projet.emplacement_archive}")
            
            # Vérifier les statistiques
            stats = StatistiqueEcart.query.filter_by(projet_id=3).first()
            if stats:
                print(f"✅ Statistiques trouvées:")
                print(f"   Fichier1 unique: {stats.nb_ecarts_uniquement_fichier1}")
                print(f"   Fichier2 unique: {stats.nb_ecarts_uniquement_fichier2}")
                print(f"   Communs: {stats.nb_ecarts_communs}")
                print(f"   Date: {stats.date_execution}")
            else:
                print("⚠️ Aucune statistique trouvée pour ce projet")
            
            # Test de la route
            with app.test_client() as client:
                response = client.get('/projet-details/3')
                print(f"🌐 Status HTTP: {response.status_code}")
                
                data = response.get_json()
                if response.status_code == 200:
                    print("✅ Succès! Données reçues:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print("❌ Erreur:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
        except Exception as e:
            print(f"❌ Erreur globale: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_projet_3()
