import os

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or '12GQSGQza&ç_çàFAFSF'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Folder configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads/source')
    
    # Active ou non l'auto migration (utile pour ne pas migrer en prod automatiquement)
    AUTO_MIGRATION = os.environ.get('AUTO_MIGRATION', 'false').lower() == 'true'
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ENABLE_GPT_PROCESSING = os.environ.get('ENABLE_GPT_PROCESSING', 'false').lower() == 'true'
    
    # Database configuration avec retry et timeout
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'connect_timeout': 60,
            'read_timeout': 30,
            'write_timeout': 30
        }
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'
    
    # Utiliser DATABASE_URL d'abord, puis DEV_DATABASE_URL, puis fallback local
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or 
        os.environ.get('DEV_DATABASE_URL') or 
        'mysql+pymysql://DataAlign:DataAlign@localhost:3306/DataAlign_dev?charset=utf8mb4'
    )

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'
    
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or 
        'mysql+pymysql://DataAlign:DataAlign@localhost/DataAlign_prod?charset=utf8mb4'
    )
    
    # Configuration SSL pour la production si nécessaire
    # SQLALCHEMY_ENGINE_OPTIONS = {
    #     **Config.SQLALCHEMY_ENGINE_OPTIONS,
    #     'connect_args': {
    #         **Config.SQLALCHEMY_ENGINE_OPTIONS['connect_args'],
    #         'ssl_ca': '/path/to/ca.pem',
    #         'ssl_disabled': False
    #     }
    # }

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    ENV = 'testing'
    
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('TEST_DATABASE_URL') or 
        'mysql+pymysql://DataAlign:DataAlign@localhost/DataAlign_test?charset=utf8mb4'
    )

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Debug: afficher la configuration utilisée si on est en développement
if __name__ == "__main__":
    env = os.environ.get('FLASK_ENV', 'development')
    config_class = config.get(env, DevelopmentConfig)
    
    print(f"🔧 Configuration pour l'environnement: {env}")
    print(f"📊 Database URI: {config_class.SQLALCHEMY_DATABASE_URI}")
    print(f"🔒 Secret Key: {'***' + config_class.SECRET_KEY[-4:] if config_class.SECRET_KEY else 'Not set'}")
    print(f"📁 Upload Folder: {config_class.UPLOAD_FOLDER}")
    print(f"🔄 Auto Migration: {config_class.AUTO_MIGRATION}")
    print(f"🐛 Debug Mode: {getattr(config_class, 'DEBUG', False)}")