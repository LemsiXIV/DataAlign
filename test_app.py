#!/usr/bin/env python3
"""
Script pour tester l'application complète
"""
from app import create_app
import threading
import time
import webbrowser

def start_app():
    """Démarrer l'application Flask"""
    app = create_app()
    app.run(debug=True, port=5000, host='127.0.0.1', use_reloader=False)

def test_app():
    """Tester l'application"""
    print("🚀 Démarrage de l'application Flask...")
    
    # Démarrer l'app dans un thread séparé
    app_thread = threading.Thread(target=start_app, daemon=True)
    app_thread.start()
    
    # Attendre que l'app soit prête
    time.sleep(3)
    
    print("🌐 Application démarrée sur http://127.0.0.1:5000")
    print("📊 Dashboard disponible sur http://127.0.0.1:5000/dashboard")
    print("👆 Cliquez sur un bouton 'Détails' pour tester")
    
    # Optionnel: ouvrir le navigateur automatiquement
    try:
        webbrowser.open('http://127.0.0.1:5000/dashboard')
    except:
        pass
    
    print("⏹️ Appuyez sur Ctrl+C pour arrêter l'application")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Application arrêtée")

if __name__ == "__main__":
    test_app()
