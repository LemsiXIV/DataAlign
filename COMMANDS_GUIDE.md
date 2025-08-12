# 🔧 Guide de Commandes DataAlign

## 🚀 Commandes de Démarrage Rapide

### Installation Complète (Recommandé)
```bash
# Déploiement automatisé complet
python deploy.py
```

### Installation Manuelle Étape par Étape
```bash
# 1. Désactiver les migrations automatiques  
python disable_migrations.py

# 2. Initialiser la base de données
python bypass_migrations.py

# 3. Maintenance et vérification
python maintenance.py

# 4. Démarrage application
python start_production.py
```

## 🛠️ Scripts de Maintenance

### Scripts Principaux
| Script | Usage | Description |
|--------|--------|-------------|
| `maintenance.py` | `python maintenance.py` | Maintenance complète du système |
| `bypass_migrations.py` | `python bypass_migrations.py` | Contournement migrations Alembic |
| `disable_migrations.py` | `python disable_migrations.py` | Désactivation permanente migrations |
| `test_password_reset.py` | `python test_password_reset.py` | Test système reset password |

### Scripts Spécialisés
| Script | Usage | Description |
|--------|--------|-------------|
| `fix_database.py` | `python fix_database.py` | Corrections spécifiques BDD |
| `create_initial_users.py` | `python create_initial_users.py` | Création comptes de test |
| `add_password_reset_fields.py` | `python add_password_reset_fields.py` | Ajout champs reset en BDD |

## 🚀 Commandes de Démarrage

### Développement
```bash
# Démarrage simple
python run.py

# Avec configuration
python start_without_migrations.py

# Production locale
python start_production.py
```

### Production
```bash
# Installation Gunicorn
pip install gunicorn

# Démarrage production
gunicorn -w 4 -b 0.0.0.0:5000 'app:create_app()'

# Avec configuration personnalisée
gunicorn -c gunicorn.conf.py 'app:create_app()'
```

## 🔍 Commandes de Diagnostic

### Vérification Système
```bash
# Test complet du système
python maintenance.py

# Test spécifique reset password
python test_password_reset.py

# Vérification base de données
python bypass_migrations.py --check

# Status des migrations
python -c "from app import create_app; app = create_app(); print('App créée avec succès')"
```

### Logs et Monitoring
```bash
# Voir logs en temps réel (Unix/Linux)
tail -f logs/dataalign.log

# Logs Windows
Get-Content logs/dataalign.log -Wait

# Vérifier processus
ps aux | grep python  # Unix/Linux
Get-Process python    # Windows
```

## 🗄️ Commandes Base de Données

### Gestion SQLite (Développement)
```bash
# Ouvrir base SQLite
sqlite3 dataalign.db

# Vérifier structure
sqlite3 dataalign.db ".schema users"

# Backup base
cp dataalign.db dataalign_backup_$(date +%Y%m%d).db
```

### Gestion MySQL (Production)
```bash
# Backup
mysqldump -u dataalign_user -p dataalign_prod > backup_$(date +%Y%m%d).sql

# Restore
mysql -u dataalign_user -p dataalign_prod < backup_file.sql

# Vérifier structure
mysql -u dataalign_user -p -e "DESCRIBE dataalign_prod.users;"
```

### Gestion PostgreSQL (Production)
```bash
# Backup
pg_dump -U dataalign_user dataalign_prod > backup_$(date +%Y%m%d).sql

# Restore
psql -U dataalign_user dataalign_prod < backup_file.sql

# Vérifier structure
psql -U dataalign_user -d dataalign_prod -c "\d users"
```

## 🔧 Commandes de Configuration

### Variables d'Environnement
```bash
# Créer fichier .env
cp .env.example .env

# Générer clé secrète
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Vérifier configuration
python -c "from app.config import Config; print('Config OK')"
```

### Permissions (Unix/Linux)
```bash
# Permissions répertoires
chmod 755 uploads logs temp
chmod 600 .env

# Propriétaire fichiers
chown -R www-data:www-data ./
```

## 📦 Gestion des Dépendances

### Python Packages
```bash
# Installer dépendances
pip install -r requirements.txt

# Mettre à jour pip
pip install --upgrade pip

# Packages critiques individuels
pip install flask flask-sqlalchemy flask-login flask-mail werkzeug alembic
```

### Environnement Virtuel
```bash
# Créer environnement virtuel
python -m venv venv

# Activer (Unix/Linux)
source venv/bin/activate

# Activer (Windows)
venv\Scripts\activate

# Désactiver
deactivate
```

## 🌐 Commandes Réseau et URLs

### Tests de Connectivité
```bash
# Test application locale
curl http://127.0.0.1:5000/

# Test endpoint spécifique
curl http://127.0.0.1:5000/auth/login

# Test avec headers
curl -H "Content-Type: application/json" http://127.0.0.1:5000/api/projets
```

### Ports et Services
```bash
# Vérifier port 5000
netstat -tulpn | grep :5000  # Unix/Linux
netstat -an | findstr :5000  # Windows

# Tuer processus sur port
kill $(lsof -ti:5000)        # Unix/Linux
# Windows : via Task Manager ou Get-Process
```

## 🛡️ Commandes de Sécurité

### Sauvegarde
```bash
# Sauvegarde complète
python backup.py

# Sauvegarde manuelle
tar -czf dataalign_backup_$(date +%Y%m%d).tar.gz ./ --exclude=__pycache__ --exclude=*.pyc

# Vérifier sauvegarde
tar -tzf dataalign_backup_*.tar.gz | head
```

### Logs de Sécurité
```bash
# Logs accès (si nginx)
tail -f /var/log/nginx/dataalign_access.log

# Logs erreurs
tail -f logs/dataalign.log | grep ERROR

# Logs authentification
grep "login\|password\|reset" logs/dataalign.log
```

## 🔄 Commandes de Mise à Jour

### Mise à Jour Application
```bash
# Backup avant mise à jour
python backup.py

# Mise à jour dépendances
pip install -r requirements.txt --upgrade

# Re-initialisation BDD si nécessaire
python bypass_migrations.py

# Test après mise à jour
python test_password_reset.py
```

### Mise à Jour Base de Données
```bash
# Mise à jour schema
python add_password_reset_fields.py

# Correction problèmes spécifiques
python fix_database.py

# Vérification intégrité
python maintenance.py
```

## 🆘 Commandes d'Urgence

### Récupération Système
```bash
# Reset complet migrations
rm -f migrations/versions/*.py  # ATTENTION : supprime l'historique
python bypass_migrations.py

# Recréation utilisateurs
python create_initial_users.py

# Reset tokens password expirés
python -c "
from app import create_app
from app.models import User, db
app = create_app()
with app.app_context():
    users = User.query.filter(User.reset_token.isnot(None)).all()
    for user in users:
        user.clear_reset_token()
    db.session.commit()
    print(f'Tokens nettoyés pour {len(users)} utilisateurs')
"
```

### Diagnostic Rapide
```bash
# Vérification santé système
python -c "
import os
import sqlite3
from pathlib import Path

print('🔍 DIAGNOSTIC RAPIDE')
print('=' * 30)
print(f'Répertoire actuel: {os.getcwd()}')
print(f'Fichier run.py: {Path(\"run.py\").exists()}')
print(f'Fichier app/__init__.py: {Path(\"app/__init__.py\").exists()}')
print(f'Base SQLite: {Path(\"dataalign.db\").exists()}')
print(f'Migrations désactivées: {Path(\"DISABLE_AUTO_MIGRATIONS\").exists()}')

if Path('dataalign.db').exists():
    conn = sqlite3.connect('dataalign.db')
    tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
    print(f'Tables BDD: {[t[0] for t in tables]}')
    conn.close()
"
```

## 📋 Aide-Mémoire

### Erreurs Fréquentes et Solutions
```bash
# ModuleNotFoundError: No module named 'app'
# Solution:
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Unix/Linux
set PYTHONPATH=%PYTHONPATH%;%CD%          # Windows

# Migration errors
# Solution:
python disable_migrations.py
python bypass_migrations.py

# Port already in use
# Solution:
kill $(lsof -ti:5000)  # Unix/Linux
# Windows: Task Manager

# Permission denied uploads/
# Solution:
chmod 755 uploads  # Unix/Linux
# Windows: Propriétés > Sécurité
```

### Comptes par Défaut
| Utilisateur | Mot de Passe | Rôle | Usage |
|-------------|--------------|------|-------|
| `testVikinn` | `admin123` | Admin | Tests administration |
| `testuser` | `test123` | User | Tests utilisateur normal |

### URLs de Test
| URL | Description | Accès |
|-----|-------------|-------|
| `http://127.0.0.1:5000/` | Page d'accueil | Public |
| `http://127.0.0.1:5000/auth/login` | Connexion | Public |
| `http://127.0.0.1:5000/dashboard` | Dashboard | Connecté |
| `http://127.0.0.1:5000/auth/forgot-password` | Reset password | Public |
| `http://127.0.0.1:5000/auth/admin/reset-tokens` | Admin tokens | Admin seulement |

---

## 🆘 Support d'Urgence

En cas de problème critique :

1. **🔄 Redémarrage complet** : `python deploy.py`
2. **🛠️ Maintenance** : `python maintenance.py`  
3. **🗄️ Reset BDD** : `python bypass_migrations.py`
4. **📋 Diagnostic** : Commandes de diagnostic ci-dessus

**📞 Pour support technique** : Consultez les logs et la documentation complète dans `DOCUMENTATION_INDEX.md`
