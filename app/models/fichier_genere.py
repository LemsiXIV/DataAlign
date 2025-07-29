from datetime import datetime
from app import db

class FichierGenere(db.Model):
    __tablename__ = 'fichiers_generes'
    id = db.Column(db.Integer, primary_key=True)
    projet_id = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=False)
    nom_traitement_projet = db.Column(db.String(255))
    nom_fichier_excel = db.Column(db.String(255))
    nom_fichier_pdf = db.Column(db.String(255))
    nom_fichier_graphe = db.Column(db.String(255))
    chemin_archive = db.Column(db.String(255))
    date_execution = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FichierGenere {self.nom_fichier_excel}>'
