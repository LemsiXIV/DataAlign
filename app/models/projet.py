from datetime import datetime
from app import db

class Projet(db.Model):
    __tablename__ = 'projets'
    id = db.Column(db.Integer, primary_key=True)
    nom_projet = db.Column(db.String(255), nullable=False)
    date_creation = db.Column(db.DateTime,default=datetime.utcnow())
    fichier_1 = db.Column(db.String(255))
    fichier_2 = db.Column(db.String(255))
    emplacement_source = db.Column(db.String(255))
    emplacement_archive = db.Column(db.String(255))

    # Relationships
    configurations = db.relationship("ConfigurationCleComposee", backref="projet", lazy=True)
    stats = db.relationship("StatistiqueEcart", backref="projet", lazy=True)
    fichiers = db.relationship("FichierGenere", backref="projet", lazy=True)
    logs = db.relationship("LogExecution", backref="projet", lazy=True)

    def __repr__(self):
        return f'<Projet {self.nom_projet}>'
