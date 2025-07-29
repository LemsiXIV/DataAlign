#!/usr/bin/env python3
"""
Script pour démarrer l'application avec logs détaillés
"""
from app import create_app
import sys

def start_debug_server():
    """Démarrer le serveur en mode debug avec logs détaillés"""
    app = create_app()
    
    # Activer les logs de débogage
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    print("🚀 Démarrage du serveur en mode debug...")
    print("📊 Dashboard: http://127.0.0.1:5000/dashboard")
    print("⚡ Logs détaillés activés - surveillez la console")
    print("🛑 Ctrl+C pour arrêter")
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Serveur arrêté")

if __name__ == "__main__":
    start_debug_server()
