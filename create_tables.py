#!/usr/bin/env python3
"""
Script pour créer les tables manquantes dans la base de données
"""
from app import create_app, db
from app.models.fichier_genere import FichierGenere
from app.models.statistiques import StatistiqueEcart
from app.models.logs import LogExecution

def create_tables():
    """Créer toutes les tables manquantes"""
    app = create_app()
    
    with app.app_context():
        try:
            # Créer toutes les tables définies dans les modèles
            db.create_all()
            print("✅ Toutes les tables ont été créées avec succès!")
            
            # Vérifier que la table fichiers_generes existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'fichiers_generes' in inspector.get_table_names():
                print("✅ Table 'fichiers_generes' créée avec succès")
                
                # Afficher les colonnes de la table
                columns = inspector.get_columns('fichiers_generes')
                print("📋 Colonnes dans la table 'fichiers_generes':")
                for col in columns:
                    print(f"  - {col['name']} ({col['type']})")
            else:
                print("❌ Erreur: Table 'fichiers_generes' non créée")
                
        except Exception as e:
            print(f"❌ Erreur lors de la création des tables: {e}")

if __name__ == "__main__":
    create_tables()
