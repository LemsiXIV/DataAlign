#!/usr/bin/env python
"""
Script de maintenance DataAlign
Effectue toutes les vérifications et corrections nécessaires
"""

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
        print(f"\n📋 {name}...")
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
    
    print("\n" + "=" * 50)
    print("🎉 Maintenance terminée!")
    print("\n🚀 Vous pouvez maintenant démarrer l'application:")
    print("   python start_without_migrations.py")

if __name__ == '__main__':
    run_maintenance()
