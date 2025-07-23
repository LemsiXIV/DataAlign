from datetime import datetime
from app import db

class LogExecution(db.Model):
    __tablename__ = 'logs_execution'
    id = db.Column(db.Integer, primary_key=True)
    projet_id = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=False)
    statut = db.Column(db.Enum('succès', 'échec'), nullable=False)
    date_execution = db.Column(db.DateTime, default=datetime.utcnow)
    message = db.Column(db.Text)

    def __repr__(self):
        return f'<LogExecution {self.statut}>'
