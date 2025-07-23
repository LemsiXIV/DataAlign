from app import db

class ConfigurationCleComposee(db.Model):
    __tablename__ = 'configurations_cles_composees'
    id = db.Column(db.Integer, primary_key=True)
    projet_id = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=False)
    fichier = db.Column(db.Enum('fichier1', 'fichier2'), nullable=False)
    champs_concatenes = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<ConfigurationCleComposee {self.fichier}>'
