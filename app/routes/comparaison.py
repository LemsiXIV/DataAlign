from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from io import StringIO
import pandas as pd
from app import db
from app.models import Projet, ConfigurationCleComposee, StatistiqueEcart
from app.services.comparateur import ComparateurFichiers
from datetime import datetime

comparaison_bp = Blueprint('comparaison', __name__)

@comparaison_bp.route('/compare', methods=['POST'])
def compare():
    keys1 = [k.strip() for k in request.form.getlist('key1')]
    keys2 = [k.strip() for k in request.form.getlist('key2')]

    try:
        df = pd.read_json(session['df_path'])
        df2 = pd.read_json(session['df2_path'])
    except Exception as e:
        flash(f"Erreur lors du chargement des fichiers JSON : {e}", "error")
        return redirect(url_for('projets.index'))

    # Nettoyer les noms de colonnes
    df.columns = df.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    # 🔍 LOGS de débogage
    print("Clés sélectionnées fichier 1 :", keys1)
    print("Clés sélectionnées fichier 2 :", keys2)
    print("Colonnes fichier 1 :", df.columns.tolist())
    print("Colonnes fichier 2 :", df2.columns.tolist())

    # Validation des clés
    if not keys1 or not keys2:
        flash("Veuillez sélectionner au moins une clé dans chaque fichier.", "error")
        return redirect(url_for('projets.index'))
        
    if not all(k in df.columns for k in keys1) or not all(k in df2.columns for k in keys2):
        flash(f"Clés invalides sélectionnées. Colonnes disponibles : {df.columns.tolist()} vs {df2.columns.tolist()}", "error")
        return redirect(url_for('projets.index'))

    # Use the comparator service
    comparateur = ComparateurFichiers(df, df2, keys1, keys2)
    results = comparateur.comparer()

    file1_name = session.get('file1_name', 'Fichier 1')
    file2_name = session.get('file2_name', 'Fichier 2')

    # Get project ID from session
    projet_id = session.get("projet_id")

    if not projet_id:
        flash("Aucun projet sélectionné. Veuillez sélectionner un projet avant de comparer.", "error")
        return redirect(url_for('projets.index'))

    # Save configurations
    config1 = ConfigurationCleComposee(
        projet_id=projet_id,
        fichier='fichier1',
        champs_concatenes=','.join(keys1)
    )
    config2 = ConfigurationCleComposee(
        projet_id=projet_id,
        fichier='fichier2',
        champs_concatenes=','.join(keys2)
    )
    db.session.add_all([config1, config2])

    # Save statistics
    stat = StatistiqueEcart(
        projet_id=projet_id,
        nb_ecarts_uniquement_fichier1=results['n1'],
        nb_ecarts_uniquement_fichier2=results['n2'],
        nb_ecarts_communs=results['n_common'],
        date_execution=datetime.now()
    )
    db.session.add(stat)

    db.session.commit()

    return render_template("compare.html",
                           key1=' + '.join(keys1),
                           key2=' + '.join(keys2),
                           ecarts1=results['ecarts_fichier1'].to_dict(orient='records'),
                           ecarts2=results['ecarts_fichier2'].to_dict(orient='records'),
                           file1_name=file1_name,
                           file2_name=file2_name,
                           **results)

@comparaison_bp.route('/Fast_Compare', methods=['POST'])
def fast_compare():
    try:
        df = pd.read_json(session['df_path'])
        df2 = pd.read_json(session['df2_path'])
    except Exception as e:
        flash(f"Erreur lors de la lecture des fichiers JSON : {e}", "error")
        return redirect(url_for('projets.index'))

    keys1 = [k.strip() for k in request.form.getlist('key1')]
    keys2 = [k.strip() for k in request.form.getlist('key2')]

    # Nettoyer colonnes
    df.columns = df.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    if not keys1 or not keys2:
        flash("Veuillez sélectionner au moins une clé dans chaque fichier.", "error")
        return redirect(url_for('projets.index'))

    if not all(k in df.columns for k in keys1) or not all(k in df2.columns for k in keys2):
        flash("Clés invalides sélectionnées.", "error")
        return redirect(url_for('projets.index'))

    # Appeler ton comparateur personnalisé
    comparateur = ComparateurFichiers(df, df2, keys1, keys2)
    results = comparateur.comparer()

    return render_template("compare.html",
                           key1=' + '.join(keys1),
                           key2=' + '.join(keys2),
                           ecarts1=results['ecarts_fichier1'].to_dict(orient='records'),
                           ecarts2=results['ecarts_fichier2'].to_dict(orient='records'),
                           file1_name=session.get('file1_name', 'Fichier 1'),
                           file2_name=session.get('file2_name', 'Fichier 2'),
                           **results)
