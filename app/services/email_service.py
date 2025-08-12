"""
Service pour l'envoi d'emails
Pour l'instant, ce service simule l'envoi d'emails.
Plus tard, vous pourrez intégrer un vrai service comme SendGrid, AWS SES, etc.
"""

import os
import logging
from datetime import datetime

def send_reset_email(email, full_name, reset_url):
    """
    Simule l'envoi d'un email de réinitialisation de mot de passe
    
    Args:
        email (str): Adresse email du destinataire
        full_name (str): Nom complet de l'utilisateur
        reset_url (str): URL de réinitialisation avec token
    
    Returns:
        bool: True si l'email a été "envoyé" avec succès
    """
    try:
        # Pour l'instant, on simule l'envoi en loggant les informations
        email_content = f"""
        === EMAIL DE RÉINITIALISATION DATAALIGN ===
        
        À: {email}
        Nom: {full_name}
        Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        
        Bonjour {full_name},
        
        Vous avez demandé la réinitialisation de votre mot de passe pour DataAlign.
        
        Cliquez sur le lien suivant pour créer un nouveau mot de passe :
        {reset_url}
        
        Ce lien est valide pendant 24 heures.
        
        Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
        
        Cordialement,
        L'équipe DataAlign
        
        ==========================================
        """
        
        print(email_content)
        
        # Log dans un fichier pour les admins
        log_dir = "temp"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, "password_reset_emails.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{email_content}\n")
        
        return True
        
    except Exception as e:
        logging.error(f"Erreur lors de la simulation d'envoi d'email: {e}")
        return False

def configure_real_email_service():
    """
    Configuration pour un vrai service d'email
    À implémenter plus tard avec SendGrid, AWS SES, ou SMTP
    """
    # Exemple de configuration pour SendGrid
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    
    # Exemple de configuration pour SMTP
    smtp_config = {
        'host': os.environ.get('SMTP_HOST', 'smtp.gmail.com'),
        'port': int(os.environ.get('SMTP_PORT', 587)),
        'username': os.environ.get('SMTP_USERNAME'),
        'password': os.environ.get('SMTP_PASSWORD'),
        'use_tls': True
    }
    
    return {
        'sendgrid_api_key': sendgrid_api_key,
        'smtp_config': smtp_config
    }

# TODO: Implémenter l'envoi réel d'emails
def send_real_email(email, subject, html_content, text_content=None):
    """
    Fonction pour envoyer de vrais emails
    À implémenter avec votre service d'email préféré
    """
    pass
