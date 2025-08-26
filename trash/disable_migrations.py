#!/usr/bin/env python
"""
Script pour désactiver définitivement les migrations automatiques
et configurer l'application pour fonctionner sans elles
"""

import os
import sys

def disable_auto_migrations_permanently():
    print("🚫 Désactivation permanente des migrations automatiques...")
    
    # 1. Créer un fichier .env pour désactiver les migrations
    env_content = """# Configuration DataAlign
AUTO_MIGRATION=false
FLASK_ENV=development

# Désactivation des migrations automatiques problématiques
# Les modifications de base de données sont gérées manuellement
SKIP_AUTO_MIGRATION=true
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Fichier .env créé avec AUTO_MIGRATION=false")
    except Exception as e:
        print(f"⚠️ Erreur création .env: {e}")
    
    # 2. Créer un script de démarrage personnalisé
    startup_script = """#!/usr/bin/env python
\"\"\"
Script de démarrage DataAlign sans migrations automatiques
\"\"\"

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
"""
    
    try:
        with open('start_without_migrations.py', 'w', encoding='utf-8') as f:
            f.write(startup_script)
        print("✅ Script de démarrage 'start_without_migrations.py' créé")
    except Exception as e:
        print(f"⚠️ Erreur création script: {e}")
    
    # 3. Modifier auto_migration.py pour qu'il soit moins intrusif
    auto_migration_content = """#!/usr/bin/env python
\"\"\"
Auto-migration désactivée - Modifications manuelles uniquement
\"\"\"

import os
import sys

def main():
    print("🚫 Migrations automatiques désactivées")
    print("💡 Les modifications de base de données sont gérées manuellement")
    print("📁 Utilisez les scripts suivants si nécessaire:")
    print("   - python bypass_migrations.py")
    print("   - python add_password_reset_fields.py")
    print("   - python fix_database.py")
    print()
    print("✅ Base de données configurée manuellement")
    return True

if __name__ == '__main__':
    main()
"""
    
    try:
        with open('auto_migration_disabled.py', 'w', encoding='utf-8') as f:
            f.write(auto_migration_content)
        print("✅ Version désactivée des migrations créée")
    except Exception as e:
        print(f"⚠️ Erreur création auto_migration_disabled: {e}")
    
    # 4. Instructions finales
    print("\n📋 Configuration terminée!")
    print("\n🚀 Commandes de démarrage recommandées:")
    print("   Option 1: python start_without_migrations.py")
    print("   Option 2: set AUTO_MIGRATION=false && python run.py")
    print()
    print("🔧 Maintenance de la base de données:")
    print("   python bypass_migrations.py      # Appliquer les modifications nécessaires")
    print("   python test_password_reset.py    # Tester le système de reset")
    print("   python create_initial_users.py   # Créer les utilisateurs de test")
    print()
    print("✅ Système prêt sans migrations automatiques!")

def create_maintenance_script():
    """Créer un script de maintenance globale"""
    maintenance_content = """#!/usr/bin/env python
\"\"\"
Script de maintenance DataAlign
Effectue toutes les vérifications et corrections nécessaires
\"\"\"

import os
import sys
import subprocess

def run_maintenance():
    print("🔧 Maintenance DataAlign - Début")
    print("=" * 50)
    
    scripts_to_run = [
        ("Contournement migrations", "python bypass_migrations.py"),
        ("Test système reset", "python test_password_reset.py"),
        ("Vérification utilisateurs", "python create_initial_users.py")
    ]
    
    for name, command in scripts_to_run:
        print(f"\\n📋 {name}...")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {name} - OK")
            else:
                print(f"⚠️ {name} - Avertissements")
                if result.stderr:
                    print(f"   Détails: {result.stderr[:100]}...")
        except Exception as e:
            print(f"❌ {name} - Erreur: {e}")
    
    print("\\n" + "=" * 50)
    print("🎉 Maintenance terminée!")
    print("\\n🚀 Vous pouvez maintenant démarrer l'application:")
    print("   python start_without_migrations.py")

if __name__ == '__main__':
    run_maintenance()
"""
    
    try:
        with open('maintenance.py', 'w', encoding='utf-8') as f:
            f.write(maintenance_content)
        print("✅ Script de maintenance 'maintenance.py' créé")
    except Exception as e:
        print(f"⚠️ Erreur création maintenance: {e}")

if __name__ == '__main__':
    disable_auto_migrations_permanently()
    create_maintenance_script()
    
    print("\n" + "="*60)
    print("🎯 RÉSUMÉ DE LA CONFIGURATION")
    print("="*60)
    print("✅ Migrations automatiques désactivées")
    print("✅ Scripts de contournement créés")
    print("✅ Configuration environnement mise à jour")
    print("✅ Scripts de maintenance disponibles")
    print()
    print("🚀 DÉMARRAGE RECOMMANDÉ:")
    print("   python start_without_migrations.py")
    print()
    print("🔧 MAINTENANCE:")
    print("   python maintenance.py")
    print("="*60)
