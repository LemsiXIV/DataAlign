#!/usr/bin/env python3
"""
Script pour exécuter manuellement les migrations automatiques
"""

from app import create_app
from auto_migration import init_auto_migration

def main():
    """Exécuter les migrations manuellement"""
    print("=== Exécution manuelle des migrations ===")
    
    app = create_app()
    
    # Temporairement activer AUTO_MIGRATION pour cette exécution
    app.config['AUTO_MIGRATION'] = True
    
    try:
        init_auto_migration(app)
        print("✅ Migrations terminées avec succès")
    except Exception as e:
        print(f"❌ Erreur lors des migrations: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
