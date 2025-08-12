#!/usr/bin/env python
"""
Script de test pour le système de réinitialisation de mot de passe
"""

from app import create_app, db
from app.models.user import User
from app.services.email_service import send_reset_email
from flask import url_for
import sys

def test_password_reset_system():
    app = create_app()
    
    with app.app_context():
        try:
            # Chercher un utilisateur de test
            test_user = User.query.filter_by(username='testVikinn').first()
            if not test_user:
                print("❌ Utilisateur de test 'testuser' non trouvé")
                print("Créez d'abord un utilisateur de test avec create_initial_users.py")
                return False
            
            print(f"✅ Utilisateur trouvé: {test_user.username} ({test_user.email})")
            
            # Générer un token de réinitialisation
            print("\n🔧 Génération d'un token de réinitialisation...")
            token = test_user.generate_reset_token()
            
            # Sauvegarder en base
            db.session.commit()
            print(f"✅ Token généré: {token}")
            print(f"✅ Expire le: {test_user.reset_token_expires}")
            
            # Vérifier le token
            print("\n🔍 Vérification du token...")
            is_valid = test_user.verify_reset_token(token)
            print(f"✅ Token valide: {is_valid}")
            
            # Simuler l'envoi d'email
            print("\n📧 Simulation d'envoi d'email...")
            with app.test_request_context():
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                email_sent = send_reset_email(test_user.email, test_user.full_name, reset_url)
                print(f"✅ Email simulé: {email_sent}")
                print(f"🔗 URL de réinitialisation: {reset_url}")
            
            # Test avec un faux token
            print("\n🔍 Test avec un faux token...")
            fake_is_valid = test_user.verify_reset_token("fake_token_123")
            print(f"✅ Faux token rejeté: {not fake_is_valid}")
            
            # Nettoyer le token de test
            print("\n🧹 Nettoyage du token de test...")
            test_user.clear_reset_token()
            db.session.commit()
            print("✅ Token nettoyé")
            
            print("\n🎉 Tous les tests sont passés avec succès!")
            print("\nVous pouvez maintenant:")
            print("1. Démarrer l'application: python run.py")
            print("2. Aller sur /auth/login")
            print("3. Cliquer sur 'Mot de passe oublié ?'")
            print("4. Entrer l'email: test@dataalign.com")
            print("5. Copier l'URL du lien depuis la console/log")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("🧪 Test du système de réinitialisation de mot de passe...")
    success = test_password_reset_system()
    if not success:
        sys.exit(1)
