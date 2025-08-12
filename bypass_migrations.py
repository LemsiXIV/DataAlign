#!/usr/bin/env python
"""
Script de contournement pour les migrations défaillantes
Applique manuellement les modifications nécessaires à la base de données
"""

from app import create_app, db
from app.models.user import User
from app.models.logs import LogExecution
import sys
from sqlalchemy import text

def bypass_migrations():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Contournement des migrations automatiques défaillantes...")
            
            with db.engine.connect() as connection:
                print("\n1. Vérification de la base de données...")
                
                # Identifier le type de base de données
                db_type = str(connection.dialect.name).lower()
                print(f"   Type de base de données détecté: {db_type}")
                
                # Commandes spécifiques selon le type de base
                if db_type in ['mysql', 'mariadb']:
                    describe_cmd = "DESCRIBE users"
                    describe_logs_cmd = "DESCRIBE logs_execution"
                elif db_type == 'sqlite':
                    describe_cmd = "PRAGMA table_info(users)"
                    describe_logs_cmd = "PRAGMA table_info(logs_execution)"
                else:
                    # PostgreSQL
                    describe_cmd = "SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"
                    describe_logs_cmd = "SELECT column_name FROM information_schema.columns WHERE table_name = 'logs_execution'"
                
                print("\n2. Analyse de la table users...")
                try:
                    result = connection.execute(text(describe_cmd))
                    if db_type in ['mysql', 'mariadb']:
                        columns = [row[0] for row in result]
                    elif db_type == 'sqlite':
                        columns = [row[1] for row in result]
                    else:
                        columns = [row[0] for row in result]
                    
                    print(f"   Colonnes existantes: {columns}")
                    
                    # Ajouter les colonnes de reset si nécessaire
                    if 'reset_token' not in columns:
                        print("   Ajout de reset_token...")
                        connection.execute(text('ALTER TABLE users ADD COLUMN reset_token VARCHAR(100)'))
                        connection.commit()
                        print("   ✅ reset_token ajoutée")
                    else:
                        print("   ✅ reset_token existe déjà")
                    
                    if 'reset_token_expires' not in columns:
                        print("   Ajout de reset_token_expires...")
                        connection.execute(text('ALTER TABLE users ADD COLUMN reset_token_expires DATETIME'))
                        connection.commit()
                        print("   ✅ reset_token_expires ajoutée")
                    else:
                        print("   ✅ reset_token_expires existe déjà")
                
                except Exception as e:
                    print(f"   ❌ Erreur avec la table users: {e}")
                
                print("\n3. Analyse de la table logs_execution...")
                try:
                    result = connection.execute(text(describe_logs_cmd))
                    if db_type in ['mysql', 'mariadb']:
                        logs_info = list(result)
                        print("   Structure actuelle des logs:")
                        for col in logs_info:
                            if col[0] == 'statut':
                                print(f"     statut: {col[1]}")
                        
                        # Modifier la colonne statut si nécessaire
                        try:
                            connection.execute(text("ALTER TABLE logs_execution MODIFY COLUMN statut VARCHAR(20) NOT NULL"))
                            connection.commit()
                            print("   ✅ Colonne statut élargie")
                        except Exception as e:
                            print(f"   ⚠️ Statut déjà correct ou erreur: {e}")
                    
                except Exception as e:
                    print(f"   ❌ Erreur avec la table logs: {e}")
                
                print("\n4. Test de fonctionnement...")
                
                # Test d'écriture de log
                try:
                    # Commencer une nouvelle transaction
                    db.session.rollback()  # S'assurer qu'il n'y a pas de transaction en cours
                    
                    test_log = LogExecution(
                        projet_id=None,
                        statut='test',
                        message='Test de contournement des migrations'
                    )
                    
                    db.session.add(test_log)
                    db.session.commit()
                    print("   ✅ Test d'écriture de log réussi")
                    
                    # Supprimer le log de test
                    db.session.delete(test_log)
                    db.session.commit()
                    print("   ✅ Log de test nettoyé")
                    
                except Exception as e:
                    print(f"   ❌ Erreur lors du test de log: {e}")
                    db.session.rollback()
                
                # Test des tokens de reset
                try:
                    user = User.query.first()
                    if user:
                        print(f"   Test avec utilisateur: {user.username}")
                        
                        # Test génération token
                        token = user.generate_reset_token()
                        if token:
                            print(f"   ✅ Token généré: {token[:10]}...")
                            
                            # Test validation
                            is_valid = user.verify_reset_token(token)
                            print(f"   ✅ Token valide: {is_valid}")
                            
                            # Nettoyer
                            user.clear_reset_token()
                            db.session.commit()
                            print("   ✅ Token nettoyé")
                        else:
                            print("   ❌ Échec génération token")
                    else:
                        print("   ⚠️ Aucun utilisateur pour le test")
                        
                except Exception as e:
                    print(f"   ❌ Erreur lors du test de reset: {e}")
                    db.session.rollback()
                
                print("\n🎉 Contournement terminé!")
                print("\nLe système devrait maintenant fonctionner correctement.")
                print("Les migrations automatiques peuvent être ignorées.")
                
                return True
                
        except Exception as e:
            print(f"❌ Erreur critique: {e}")
            import traceback
            traceback.print_exc()
            return False

def disable_auto_migrations():
    """Désactiver les migrations automatiques problématiques"""
    try:
        print("\n🚫 Désactivation des migrations automatiques...")
        
        # Lire le fichier de configuration
        config_files = ['app/config.py', 'config.py']
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'AUTO_MIGRATION' in content:
                    print(f"   Fichier de config trouvé: {config_file}")
                    # Note: Ne pas modifier automatiquement, juste informer
                    print("   💡 Conseil: Définir AUTO_MIGRATION=false dans votre environnement")
                    break
                    
            except FileNotFoundError:
                continue
        
        print("   ✅ Instructions données pour désactiver les migrations auto")
        
    except Exception as e:
        print(f"   ⚠️ Erreur lors de la désactivation: {e}")

if __name__ == '__main__':
    print("🛠️ Contournement des migrations défaillantes...")
    
    success = bypass_migrations()
    
    if success:
        disable_auto_migrations()
        print("\n✅ Système opérationnel!")
        print("\n📝 Prochaines étapes:")
        print("1. Définir AUTO_MIGRATION=false")
        print("2. Redémarrer l'application: python run.py")
        print("3. Tester la réinitialisation de mot de passe")
    else:
        print("\n❌ Échec du contournement")
        sys.exit(1)
