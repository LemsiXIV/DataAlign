from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize extensions
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # Configuration
    app.secret_key = '12GQSGQza&ç_çàFAFSF'
    
    # Database Setup
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://DataAlign:DataAlign@localhost/DataAlign'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Folder Setup
    UPLOAD_FOLDER = 'uploads/source'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Archive Folder
    ARCHIVE_FOLDER = 'archive'
    app.config['ARCHIVE_FOLDER'] = ARCHIVE_FOLDER
    os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    
    # Import models after db initialization to avoid circular imports
    from app.models import Projet, ConfigurationCleComposee, StatistiqueEcart, FichierGenere, LogExecution
    
    # Register blueprints
    from app.routes.projets import projets_bp
    from app.routes.comparaison import comparaison_bp
    from app.routes.fichiers import fichiers_bp
    
    app.register_blueprint(projets_bp)
    app.register_blueprint(comparaison_bp)
    app.register_blueprint(fichiers_bp)
    
    return app