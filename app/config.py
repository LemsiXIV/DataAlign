import os

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or '12GQSGQza&ç_çàFAFSF'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Folder configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads/source')
   
    
    # Active ou non l'auto migration (utile pour ne pas migrer en prod automatiquement)
    AUTO_MIGRATION = os.environ.get('AUTO_MIGRATION', 'false').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql+pymysql://DataAlign:DataAlign@localhost/DataAlign_dev'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://DataAlign:DataAlign@localhost/DataAlign_prod'



class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    ENV = 'testing'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://DataAlign:DataAlign@localhost/DataAlign_test'
   



config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
# This file defines the configuration for the Flask application
# It includes different configurations for development, production, and testing environments