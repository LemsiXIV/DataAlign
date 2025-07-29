#!/usr/bin/env python3
"""
Test rapide pour vérifier la correction du problème de projet ID
"""
from app import create_app
from app.models import Projet

def test_dashboard_data():
    """Test des données du dashboard"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Vérification des projets existants...")
        projets = Projet.query.all()
        
        for projet in projets:
            print(f"📊 Projet ID: {projet.id} - Nom: {projet.nom_projet}")
            print(f"   Date: {projet.date_creation}")
            print(f"   Archive: {projet.emplacement_archive}")
            
        print(f"\n✅ Total projets: {len(projets)}")
        
        # Test spécifique pour les projets visibles
        print("\n🎯 Test de la route projet-details pour chaque projet:")
        with app.test_client() as client:
            for projet in projets:
                response = client.get(f'/projet-details/{projet.id}')
                status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
                print(f"   Projet {projet.id}: {status}")

if __name__ == "__main__":
    test_dashboard_data()
