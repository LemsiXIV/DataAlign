# DataAlign - Automatisation DRC

DataAlign est une application web Flask conçue pour automatiser les processus de Data Reconciliation Control (DRC). Cette plateforme permet de comparer, analyser et traiter des fichiers de données avec génération de rapports détaillés.

## ⚡ Démarrage Rapide

```bash
# Installation et configuration
pip install -r requirements.txt
python maintenance.py
python create_initial_users.py

# Démarrage de l'application
python start_without_migrations.py
```

**🌐 Application : http://127.0.0.1:5000**
**👤 Admin : testVikinn / admin123**
**🔐 Reset de mot de passe disponible**

## 🚀 Fonctionnalités

### 🔐 Authentification et Sécurité
- **Système de réinitialisation de mot de passe** : Tokens sécurisés avec expiration automatique
- **Contrôle d'accès utilisateur** : Utilisateurs voient uniquement leurs projets
- **Panel d'administration** : Gestion des tokens et utilisateurs
- **Interface responsive** : Indicateurs visuels du contexte utilisateur

### Gestion des Projets
- **Création de projets** : Interface intuitive pour créer et configurer de nouveaux projets de traitement
- **Tableau de bord** : Vue d'ensemble des projets avec métriques et statistiques
- **Gestion des utilisateurs** : Système d'authentification avec contrôle d'accès basé sur les rôles

### Traitement des Données
- **Comparaison de fichiers** : Analyse comparative entre fichiers sources et cibles
- **Support multi-formats** : Compatible avec CSV, Excel et autres formats de données
- **Détection d'écarts** : Identification automatique des différences entre les datasets

### Visualisation et Rapports
- **Graphiques d'évolution** : Visualisation des écarts dans le temps avec Chart.js
- **Rapports PDF** : Génération automatique de rapports détaillés
- **Export Excel** : Extraction des données analysées au format Excel
- **Statistiques en temps réel** : Métriques de performance et d'écarts

### Sécurité et Permissions
- **Authentification utilisateur** : Système de connexion sécurisé
- **Contrôle d'accès** : Les utilisateurs voient uniquement leurs projets, les admins ont accès à tout
- **Audit des modifications** : Historique des migrations et modifications

## 📋 Prérequis

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

