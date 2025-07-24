from datetime import datetime
from app import db

class MigrationHistory(db.Model):
    """Modèle pour stocker l'historique des migrations automatiques"""
    __tablename__ = 'migration_history'
    
    id = db.Column(db.Integer, primary_key=True)
    migration_name = db.Column(db.String(255), nullable=False)
    migration_type = db.Column(db.Enum('schema_change', 'table_creation', 'index_creation', 'data_migration'), nullable=False)
    status = db.Column(db.Enum('succès', 'échec', 'en_cours'), nullable=False)
    date_execution = db.Column(db.DateTime, default=datetime.utcnow)
    schema_hash_before = db.Column(db.String(32))  # Hash MD5
    schema_hash_after = db.Column(db.String(32))   # Hash MD5
    message = db.Column(db.Text)
    details = db.Column(db.Text)
    execution_time_ms = db.Column(db.Integer)  # Temps d'exécution en millisecondes
    
    def __repr__(self):
        return f'<MigrationHistory {self.migration_name}: {self.status}>'
    
    @classmethod
    def log_migration(cls, migration_name, migration_type, status, message, 
                     schema_hash_before=None, schema_hash_after=None, 
                     details=None, execution_time_ms=None):
        """Méthode utilitaire pour enregistrer une migration"""
        migration = cls(
            migration_name=migration_name,
            migration_type=migration_type,
            status=status,
            message=message,
            schema_hash_before=schema_hash_before,
            schema_hash_after=schema_hash_after,
            details=details,
            execution_time_ms=execution_time_ms
        )
        
        db.session.add(migration)
        try:
            db.session.commit()
            return migration
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de l'enregistrement de la migration: {e}")
            return None
