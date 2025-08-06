from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from .config import config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name=None):
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    # Si aucun config_name, tente de le récupérer via variable d'environnement FLASK_ENV
    if not config_name:
        config_name = os.getenv('FLASK_ENV', 'default')

    # Charge la configuration choisie
    app.config.from_object(config.get(config_name, config['default']))

    # Initialise la clé secrète depuis la config
    app.secret_key = app.config.get('SECRET_KEY', 'default_secret')

    # Création des dossiers configurés
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
  

    # Initialisation extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import des modèles après init db (évite imports circulaires)
    from app.models import Projet, ConfigurationCleComposee
    from app.models.statistiques import StatistiqueEcart
    from app.models.fichier_genere import FichierGenere
    from app.models.logs import LogExecution

    # Register blueprints
    from app.routes.projets import projets_bp
    from app.routes.comparaison import comparaison_bp
    from app.routes.fichiers import fichiers_bp
    from app.routes.debug import debug_bp  # Temporary debug route

    app.register_blueprint(projets_bp)
    app.register_blueprint(comparaison_bp)
    app.register_blueprint(fichiers_bp)
    app.register_blueprint(debug_bp)  # Temporary for debugging

    return app
