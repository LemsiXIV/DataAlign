#!/usr/bin/env python
"""
Script de démarrage DataAlign sans migrations automatiques
"""

import os
import sys

# Forcer la désactivation des migrations
os.environ['AUTO_MIGRATION'] = 'false'
os.environ['SKIP_AUTO_MIGRATION'] = 'true'

# Importer et démarrer l'application
try:
    from app import create_app
    
    app = create_app()
    
    print("🚀 DataAlign démarré sans migrations automatiques")
    print("📍 Application disponible sur: http://127.0.0.1:5000")
    print("🔐 Système de réinitialisation de mot de passe actif")
    print("👤 Contrôle d'accès utilisateur activé")
    print()
    print("🔑 Comptes de test:")
    print("   Admin: testVikinn / admin123")
    print("   User:  testuser / test123")
    print()
    print("Press Ctrl+C to quit...")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
    
except Exception as e:
    print(f"❌ Erreur lors du démarrage: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
