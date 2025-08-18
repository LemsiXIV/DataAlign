# 📁 DataAlign v2.0

> **⚡ Voir [README_KICKSTART.md](README_KICKSTART.md) pour le guide complet de démarrage !**

## 🚀 Démarrage Ultra-Rapide

### Option 1 : Docker (Recommandé)
```bash
python docker_start.py
# Puis : http://localhost:5000
# Login : testVikinn / admin123
```

### Option 2 : Installation Classique
```bash
python deploy.py
python start_production.py
```

## ✨ Fonctionnalités v2.0
- 🔐 **Système de réinitialisation de mot de passe complet**
- 👤 **Contrôle d'accès par utilisateur** (projets privés + admin global)  
- 🐳 **Containerisation Docker** avec CI/CD GitLab
- 📱 **Interface moderne responsive**
- 🛡️ **Sécurité renforcée** avec tokens expirables

## 👥 Comptes de Test
- **Admin** : testVikinn / admin123 (accès global + gestion tokens)
- **User** : testuser / test123 (projets personnels uniquement)

## 📚 Documentation
**📖 [README_KICKSTART.md](README_KICKSTART.md) - Guide complet avec :**
- Installation et configuration détaillée
- Scripts de maintenance automatisés  
- Configuration Docker et CI/CD
- Tests et résolution de problèmes
- Déploiement production
- Interface utilisateur et fonctionnalités

---

*🎯 Pour tout ce dont vous avez besoin : [README_KICKSTART.md](README_KICKSTART.md)*

- Python 3.8+
- Flask
- SQLAlchemy
- Alembic (pour les migrations)
- Chart.js (pour les graphiques)

## 🛠️ Installation

1. **Cloner le projet**
   ```bash
   git clone <repository-url>
   cd dataalign
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration de la base de données**
   ```bash
   # Les migrations se lancent automatiquement avec AUTO_MIGRATION=true
   ```

## 🚀 Démarrage

### Mode Développement
```bash
# Option 1 : Script personnalisé (Recommandé)
python start_without_migrations.py

# Option 2 : Méthode traditionnelle
set FLASK_ENV=development
set AUTO_MIGRATION=false
python run.py
```

### Mode Production
```bash
set FLASK_ENV=production
set AUTO_MIGRATION=false
python run.py
```

### ⚠️ Problème de Migrations
En cas de problème avec les migrations automatiques :
```bash
python bypass_migrations.py    # Contournement
python maintenance.py          # Maintenance complète
```

## 📚 Documentation Complète

- **[README_PASSWORD_RESET.md](README_PASSWORD_RESET.md)** - Documentation complète du système de réinitialisation
- **[PASSWORD_RESET_SYSTEM.md](PASSWORD_RESET_SYSTEM.md)** - Guide technique détaillé

## 📁 Structure du Projet

```
dataalign/
├── app/
│   ├── models/           # Modèles de données (Projet, Utilisateur, Statistiques, etc.)
│   ├── routes/           # Routes Flask (API, comparaison, fichiers, projets)
│   ├── services/         # Services métier (comparateur, générateurs, lecteur)
│   ├── static/           # Fichiers statiques (CSS, JS, images)
│   └── templates/        # Templates HTML (Dashboard, rapports, etc.)
├── migrations/           # Scripts de migration Alembic
├── temp/                 # Fichiers temporaires
├── uploads/              # Fichiers uploadés (source, archive)
├── run.py               # Point d'entrée de l'application
└── requirements.txt     # Dépendances Python
```

## 🎯 Utilisation

### 1. Connexion
- Accédez à `http://127.0.0.1:5000`
- Connectez-vous avec vos identifiants
- ou lance python create_initial_users.py pour deux utilisateur par defaut 

### 2. Création d'un Projet
- Cliquez sur "Create a Project"
- Remplissez les informations du projet
- Uploadez vos fichiers source et cible

### 3. Analyse des Données
- Lancez la comparaison depuis le tableau de bord
- Consultez les résultats en temps réel
- Visualisez les écarts avec les graphiques d'évolution

### 4. Génération de Rapports
- Téléchargez les rapports PDF automatiquement générés
- Exportez les données au format Excel
- Consultez les statistiques détaillées

## 🔧 Configuration

### Variables d'Environnement
- `FLASK_ENV` : Mode d'exécution (development/production)
- `AUTO_MIGRATION` : Activation des migrations automatiques (true/false)

### Base de Données
- Configuration automatique avec SQLAlchemy
- Migrations gérées par Alembic
- Support SQLite par défaut, configurable pour PostgreSQL/MySQL

## 👥 Gestion des Utilisateurs

### Rôles
- **Utilisateur** : Accès limité à ses propres projets
- **Administrateur** : Accès complet à tous les projets et utilisateurs

### Permissions
- Visualisation des projets selon l'appartenance
- Téléchargement restreint aux propriétaires
- Administration réservée aux comptes administrateurs

## 📊 Métriques et Statistiques

L'application collecte et affiche :
- Nombre d'écarts détectés par projet
- Évolution des écarts dans le temps
- Statistiques de performance des traitements
- Métriques d'utilisation par utilisateur

## 🐛 Dépannage

### Problèmes Courants
1. **Erreur de migration** : Vérifiez que `AUTO_MIGRATION=true` en développement
2. **Fichiers non uploadés** : Vérifiez les permissions du dossier `uploads/`
3. **Graphiques non affichés** : Vérifiez la connexion internet pour Chart.js CDN

### Logs
- Les logs d'application sont disponibles dans l'interface web
- Nettoyage automatique des anciens logs

## 📚 Documentation Complète

### 📋 Index Documentation
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - 📚 Index complet de toute la documentation
- **[README_PASSWORD_RESET.md](README_PASSWORD_RESET.md)** - 🔐 Documentation système de réinitialisation
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - 🚀 Guide de déploiement production

### 🚀 Déploiement Ultra-Rapide
```bash
# Installation automatisée complète
python deploy.py

# Ou étape par étape :
python disable_migrations.py
python bypass_migrations.py  
python maintenance.py
python start_production.py
```

### 📖 Documentation par Sujet
| Sujet | Fichier | Description |
|-------|---------|-------------|
| **Vue d'ensemble** | `README.md` | Guide principal et démarrage rapide |
| **Reset Password** | `README_PASSWORD_RESET.md` | Documentation complète du système |
| **Déploiement** | `DEPLOYMENT_GUIDE.md` | Production, sécurité, monitoring |
| **Index complet** | `DOCUMENTATION_INDEX.md` | Navigation dans toute la doc |

La documentation couvre :
- ✅ Installation et configuration
- ✅ Utilisation du système de reset
- ✅ Administration et gestion tokens
- ✅ Scripts de maintenance et bypass
- ✅ Déploiement production avec sécurité
- ✅ Monitoring et surveillance
- ✅ Résolution de problèmes complets
- ✅ Guides de mise à jour et maintenance

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commitez vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence propriétaire. Tous droits réservés.

## 📞 Support

Pour toute question ou problème, contactez l'équipe de développement ou 
+216 25 301 941.

