#!/usr/bin/env python
"""
Script pour corriger les problèmes de base de données
"""

from app import create_app, db
from app.models.logs import LogExecution
from app.models.user import User
import sys
from sqlalchemy import text

def fix_database_issues():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Correction des problèmes de base de données...")
            
            with db.engine.connect() as connection:
                print("\n1. Correction de la colonne statut dans logs_execution...")
                
                # Vérifier la structure actuelle de la table
                result = connection.execute(text("DESCRIBE logs_execution"))
                columns_info = list(result)
                
                # Afficher les informations actuelles
                for col in columns_info:
                    if col[0] == 'statut':
                        print(f"   Colonne statut actuelle: {col[1]}")
                
                # Modifier la colonne statut pour accepter des chaînes plus longues
                try:
                    connection.execute(text("ALTER TABLE logs_execution MODIFY COLUMN statut VARCHAR(20) NOT NULL"))
                    connection.commit()
                    print("   ✅ Colonne statut élargie à VARCHAR(20)")
                except Exception as e:
                    print(f"   ⚠️ Modification de la colonne statut: {e}")
                
                print("\n2. Vérification des colonnes de reset_token dans users...")
                
                # Vérifier si les colonnes de reset existent
                result = connection.execute(text("DESCRIBE users"))
                columns = [row[0] for row in result]
                
                if 'reset_token' not in columns:
                    print("   Ajout de la colonne reset_token...")
                    connection.execute(text('ALTER TABLE users ADD COLUMN reset_token VARCHAR(100)'))
                    connection.commit()
                    print("   ✅ Colonne reset_token ajoutée")
                else:
                    print("   ✅ Colonne reset_token existe déjà")
                
                if 'reset_token_expires' not in columns:
                    print("   Ajout de la colonne reset_token_expires...")
                    connection.execute(text('ALTER TABLE users ADD COLUMN reset_token_expires DATETIME'))
                    connection.commit()
                    print("   ✅ Colonne reset_token_expires ajoutée")
                else:
                    print("   ✅ Colonne reset_token_expires existe déjà")
                
                print("\n3. Nettoyage des sessions corrompues...")
                
                # Rollback toute transaction en cours
                try:
                    db.session.rollback()
                    print("   ✅ Sessions nettoyées")
                except:
                    pass
                
                print("\n4. Test d'écriture de log...")
                
                # Tester l'écriture d'un log
                test_log = LogExecution(
                    projet_id=None,
                    statut='info',
                    message='Test de correction de base de données'
                )
                
                db.session.add(test_log)
                db.session.commit()
                print("   ✅ Test d'écriture de log réussi")
                
                # Supprimer le log de test
                db.session.delete(test_log)
                db.session.commit()
                print("   ✅ Log de test supprimé")
            
            print("\n🎉 Toutes les corrections ont été appliquées avec succès!")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la correction: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

def verify_password_reset_system():
    """Vérification rapide du système de réinitialisation"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n🔍 Vérification du système de réinitialisation...")
            
            # Chercher un utilisateur
            user = User.query.first()
            if not user:
                print("   ⚠️ Aucun utilisateur trouvé pour le test")
                return True
            
            print(f"   ✅ Utilisateur de test: {user.username}")
            
            # Tester la génération de token
            token = user.generate_reset_token()
            if token:
                print(f"   ✅ Token généré: {token[:10]}...")
                
                # Tester la validation
                is_valid = user.verify_reset_token(token)
                print(f"   ✅ Token valide: {is_valid}")
                
                # Nettoyer
                user.clear_reset_token()
                db.session.commit()
                print("   ✅ Token nettoyé")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur lors de la vérification: {e}")
            return False

if __name__ == '__main__':
    print("🛠️ Correction des problèmes de base de données DataAlign...")
    
    success = fix_database_issues()
    if success:
        verify_password_reset_system()
        print("\n✅ Base de données corrigée!")
        print("Vous pouvez maintenant redémarrer l'application.")
    else:
        print("\n❌ Échec de la correction.")
        sys.exit(1)
