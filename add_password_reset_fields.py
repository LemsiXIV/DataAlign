#!/usr/bin/env python
"""
Script pour ajouter les champs de réinitialisation de mot de passe
"""

from app import create_app, db
from app.models.user import User
import sys
from sqlalchemy import text

def add_password_reset_fields():
    app = create_app()
    
    with app.app_context():
        try:
            # Vérifier si les colonnes existent déjà
            with db.engine.connect() as connection:
                result = connection.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result]
                
                if 'reset_token' not in columns:
                    print("Ajout de la colonne reset_token...")
                    connection.execute(text('ALTER TABLE users ADD COLUMN reset_token VARCHAR(100)'))
                    connection.commit()
                    print("✅ Colonne reset_token ajoutée")
                else:
                    print("⚠️ Colonne reset_token existe déjà")
                
                if 'reset_token_expires' not in columns:
                    print("Ajout de la colonne reset_token_expires...")
                    connection.execute(text('ALTER TABLE users ADD COLUMN reset_token_expires DATETIME'))
                    connection.commit()
                    print("✅ Colonne reset_token_expires ajoutée")
                else:
                    print("⚠️ Colonne reset_token_expires existe déjà")
            
            print("🎉 Migration terminée avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("🔧 Ajout des champs de réinitialisation de mot de passe...")
    success = add_password_reset_fields()
    if success:
        print("\n✅ Les champs de réinitialisation de mot de passe ont été ajoutés!")
        print("Vous pouvez maintenant utiliser la fonctionnalité de réinitialisation.")
    else:
        print("\n❌ Échec de la migration.")
        sys.exit(1)
