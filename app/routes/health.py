from flask import Blueprint, jsonify
from app import db
from sqlalchemy import text
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """
    Endpoint de vérification de l'état de l'application
    """
    try:
        # Vérifier la connexion à la base de données
        db.session.execute(text('SELECT 1'))
        
        # Vérifier les dossiers essentiels
        required_dirs = ['uploads', 'temp', 'logs']
        missing_dirs = []
        
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                missing_dirs.append(dir_name)
        
        status = {
            'status': 'healthy' if not missing_dirs else 'degraded',
            'database': 'connected',
            'missing_directories': missing_dirs,
            'environment': os.getenv('FLASK_ENV', 'unknown')
        }
        
        return jsonify(status), 200 if not missing_dirs else 206
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'environment': os.getenv('FLASK_ENV', 'unknown')
        }), 503

@health_bp.route('/ready')
def readiness_check():
    """
    Endpoint de vérification de la disponibilité de l'application
    """
    try:
        # Test plus approfondi de la DB
        result = db.session.execute(text('SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = DATABASE()')).fetchone()
        table_count = result.count if result else 0
        
        return jsonify({
            'status': 'ready',
            'database_tables': table_count,
            'environment': os.getenv('FLASK_ENV', 'unknown')
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'error': str(e),
            'environment': os.getenv('FLASK_ENV', 'unknown')
        }), 503

@health_bp.route('/live')
def liveness_check():
    """
    Endpoint de vérification que l'application est vivante
    """
    return jsonify({
        'status': 'alive',
        'environment': os.getenv('FLASK_ENV', 'unknown')
    }), 200