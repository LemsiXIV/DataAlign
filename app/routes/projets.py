from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import Projet, StatistiqueEcart
from datetime import datetime

projets_bp = Blueprint('projets', __name__)

@projets_bp.route("/")
@projets_bp.route("/app/templates/index")
def index():
    projets = Projet.query.order_by(Projet.date_creation.desc()).all()
    return render_template('index.html', projets=projets)



@projets_bp.route('/Historique')
def dashboard():
    projets = Projet.query.all()
    stats = StatistiqueEcart.query.all()
    return render_template('Historique.html', projets=projets, stats=stats)
