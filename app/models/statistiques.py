from datetime import datetime
from app import db

class StatistiqueEcart(db.Model):
    __tablename__ = 'statistiques_ecarts'
    id = db.Column(db.Integer, primary_key=True)
    projet_id = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=False)
    nb_ecarts_uniquement_fichier1 = db.Column(db.Integer)
    nb_ecarts_uniquement_fichier2 = db.Column(db.Integer)
    nb_ecarts_communs = db.Column(db.Integer)
    date_execution = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StatistiqueEcart Project:{self.projet_id}>'
