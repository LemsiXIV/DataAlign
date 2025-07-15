from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

#creation de la variable db
db = SQLAlchemy()



class Projet(db.Model):
    __tablename__ = 'projets'
    id = db.Column(db.Integer, primary_key=True)
    nom_projet = db.Column(db.String(255), nullable=False)
    date_creation = db.Column(db.Date, default=lambda: datetime.utcnow().date())
    fichier_1 = db.Column(db.String(255))
    fichier_2 = db.Column(db.String(255))
    emplacement_source = db.Column(db.String(255))
    emplacement_archive = db.Column(db.String(255))

    configurations = db.relationship("ConfigurationCleComposee", backref="projet", lazy=True)
    stats = db.relationship("StatistiqueEcart", backref="projet", lazy=True)
    fichiers = db.relationship("FichierGenere", backref="projet", lazy=True)
    logs = db.relationship("LogExecution", backref="projet", lazy=True)


class ConfigurationCleComposee(db.Model):
    __tablename__ = 'configurations_cles_composees'
    id = db.Column(db.Integer, primary_key=True)
    projet_id = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=False)
    fichier = db.Column(db.Enum('fichier1', 'fichier2'), nullable=False)
    champs_concatenes = db.Column(db.Text, nullable=False)


class StatistiqueEcart(db.Model):
    __tablename__ = 'statistiques_ecarts'
    id = db.Column(db.Integer, primary_key=True)
    projet_id = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=False)
    nb_ecarts_uniquement_fichier1 = db.Column(db.Integer)
    nb_ecarts_uniquement_fichier2 = db.Column(db.Integer)
    nb_ecarts_communs = db.Column(db.Integer)
    date_execution = db.Column(db.DateTime, default=datetime.utcnow)


class FichierGenere(db.Model):
    __tablename__ = 'fichiers_generes'
    id = db.Column(db.Integer, primary_key=True)
    projet_id = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=False)
    nom_fichier_excel = db.Column(db.String(255))
    nom_fichier_graphe = db.Column(db.String(255))
    chemin_archive = db.Column(db.String(255))


class LogExecution(db.Model):
    __tablename__ = 'logs_execution'
    id = db.Column(db.Integer, primary_key=True)
    projet_id = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=False)
    statut = db.Column(db.Enum('succès', 'échec'), nullable=False)
    date_execution = db.Column(db.DateTime, default=datetime.utcnow)
    message = db.Column(db.Text)
