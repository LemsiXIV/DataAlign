#!/usr/bin/env python3
"""
Script pour tester la route projet_details
"""
from app import create_app
from app.models import Projet
from app.models.statistiques import StatistiqueEcart
import json

def test_projet_details():
    """Tester la route projet_details"""
    app = create_app()
    
    with app.app_context():
        try:
            # Récupérer un projet pour tester
            projets = Projet.query.all()
            if not projets:
                print("❌ Aucun projet trouvé dans la base de données")
                return
            
            projet = projets[0]
            print(f"🧪 Test avec le projet ID: {projet.id}, nom: {projet.nom_projet}")
            
            # Tester chaque partie de la fonction projet_details
            print(f"✅ Projet récupéré: {projet.nom_projet}")
            
            # Test des statistiques
            try:
                stats = StatistiqueEcart.query.filter_by(projet_id=projet.id).first()
                print(f"✅ Statistiques: {'Trouvées' if stats else 'Aucune'}")
            except Exception as e:
                print(f"❌ Erreur statistiques: {e}")
            
            # Test de l'emplacement archive
            print(f"📁 Archive: {projet.emplacement_archive}")
            
            # Test avec le client de test Flask
            with app.test_client() as client:
                response = client.get(f'/projet-details/{projet.id}')
                print(f"🌐 Status HTTP: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"📊 Données JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    print(f"❌ Erreur HTTP: {response.data.decode()}")
                    
        except Exception as e:
            print(f"❌ Erreur globale: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_projet_details()
