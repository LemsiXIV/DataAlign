#!/usr/bin/env python3
"""
Script pour exécuter manuellement les migrations automatiques
"""

from app import create_app
from auto_migration import run_migration_check

def main():
    """Exécuter les migrations manuellement"""
    print("=== Exécution manuelle des migrations ===")
    
    app = create_app()
    
    with app.app_context():
        try:
            run_migration_check()
            print("✅ Migrations terminées avec succès")
        except Exception as e:
            print(f"❌ Erreur lors des migrations: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
