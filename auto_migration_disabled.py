#!/usr/bin/env python
"""
Auto-migration désactivée - Modifications manuelles uniquement
"""

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
