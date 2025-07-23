# This file is kept for backward compatibility
# All models have been moved to app/models/
from app.models.projet import Projet
from app.models.configurations import ConfigurationCleComposee
from app.models.statistiques import StatistiqueEcart
from app.models.fichier_genere import FichierGenere
from app.models.logs import LogExecution
from flask_sqlalchemy import SQLAlchemy

# Database instance
db = SQLAlchemy()
