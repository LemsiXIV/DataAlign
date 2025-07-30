from flask.cli import FlaskGroup
from app import create_app, db
from flask_migrate import Migrate
from app.models import *  # Assure l'import des modèles

app = create_app()
migrate = Migrate(app, db)
cli = FlaskGroup(app)

if __name__ == "__main__":
    cli()
# This file is used to run the Flask application and manage migrations
# You can run it with the command: python cli.py