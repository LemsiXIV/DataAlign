from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from .config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

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
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Import des modèles après init db (évite imports circulaires)
    from app.models import Projet, ConfigurationCleComposee
    from app.models.statistiques import StatistiqueEcart
    from app.models.fichier_genere import FichierGenere
    from app.models.logs import LogExecution
    from app.models.user import User, DeletionRequest
    from app.models.notification import Notification

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.projets import projets_bp
    from app.routes.comparaison import comparaison_bp
    from app.routes.fichiers import fichiers_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.notifications import notifications_bp
    from app.routes.health import health_bp


    app.register_blueprint(projets_bp)
    app.register_blueprint(comparaison_bp)
    app.register_blueprint(fichiers_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(notifications_bp)
    app.register_blueprint(health_bp)

    # Create initial users if enabled (for Docker deployment)
    if os.getenv('CREATE_INITIAL_USERS', 'false').lower() == 'true':
        with app.app_context():
            try:
                # Ensure tables exist first
                db.create_all()
                create_default_users()
                print("✅ Initial users created successfully")
            except Exception as e:
                print(f"⚠️ Error creating initial users: {e}")

    return app

def create_default_users():
    """Create default test users for the application"""
    from app.models.user import User
    from werkzeug.security import generate_password_hash
    
    # Create admin user (testVikinn)
    admin_user = User.query.filter_by(username='testVikinn').first()
    if not admin_user:
        admin_user = User(
            username='testVikinn',
            email='admin@dataalign.com',
            full_name='Test Admin Vikinn',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            is_active=True
        )
        db.session.add(admin_user)
        print("👑 Created admin user: testVikinn / admin123")
    
    # Create regular user (testuser)
    regular_user = User.query.filter_by(username='testuser').first()
    if not regular_user:
        regular_user = User(
            username='testuser',
            email='user@dataalign.com',
            full_name='Test User',
            password_hash=generate_password_hash('test123'),
            role='user',
            is_active=True
        )
        db.session.add(regular_user)
        print("👤 Created regular user: testuser / test123")
    
    # Commit all changes
    db.session.commit()
    print("✅ Default users created successfully")
