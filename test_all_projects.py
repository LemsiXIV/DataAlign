#!/usr/bin/env python3
"""
Script pour tester tous les projets et identifier lequel pose problème
"""
from app import create_app
from app.models import Projet

def test_all_projects():
    """Tester tous les projets un par un"""
    app = create_app()
    
    with app.app_context():
        try:
            projets = Projet.query.all()
            print(f"🔍 Test de {len(projets)} projets")
            
            for projet in projets:
                print(f"\n📊 Test projet ID: {projet.id} - {projet.nom_projet}")
                
                try:
                    with app.test_client() as client:
                        response = client.get(f'/projet-details/{projet.id}')
                        if response.status_code == 200:
                            print(f"  ✅ OK - Status: {response.status_code}")
                        else:
                            print(f"  ❌ ERREUR - Status: {response.status_code}")
                            data = response.get_json()
                            print(f"     Message: {data.get('message', 'Pas de message')}")
                            
                except Exception as e:
                    print(f"  💥 EXCEPTION: {e}")
                    
        except Exception as e:
            print(f"❌ Erreur globale: {e}")

if __name__ == "__main__":
    test_all_projects()
