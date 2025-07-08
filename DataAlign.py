from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import pandas as pd
from io import StringIO 
app = Flask(__name__)
app.secret_key = '12GQSGQza&ç_çàFAFSF'



UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

# Route pour l'upload et la lecture des fichiers
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'file2' not in request.files:
        flash("Veuillez sélectionner les deux fichiers", "error")
        return redirect(url_for('index'))

    file = request.files['file']
    file2 = request.files['file2']

    if file.filename == '' or file2.filename == '':
        flash("Un des fichiers est vide", "error")
        return redirect(url_for('index'))

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)
    file.save(filepath)
    file2.save(filepath2)

    ext = file.filename.split('.')[-1].lower()

    try:
        if ext == 'csv':
            df = pd.read_csv(filepath)
        elif ext in ['xls', 'xlsx']:
            df = pd.read_excel(filepath)
        elif ext == 'json':
            df = pd.read_json(filepath)
        else:
            flash("Type de fichier non supporté", "error")
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"Erreur lors de la lecture du fichier : {e}", "error")
        return redirect(url_for('index'))

    ext2 = file2.filename.split('.')[-1].lower()
    try:
        if ext2 == 'csv':
            df2 = pd.read_csv(filepath2)
        elif ext2 in ['xls', 'xlsx']:
            df2 = pd.read_excel(filepath2)
        elif ext2 == 'json':
            df2 = pd.read_json(filepath2)
        else:
            flash("Type de fichier non supporté pour le deuxième fichier", "error")
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"Erreur lors de la lecture du deuxième fichier : {e}", "error")
        return redirect(url_for('index'))

    

    # Convertir les données en HTML pour affichage
    data = df.to_dict(orient='records')
    columns = df.columns.tolist()

    data2 = df2.to_dict(orient='records')
    columns2 = df2.columns.tolist()

    session['data'] = df.to_json()
    session['data2'] = df2.to_json()
    session['file1_name'] = file.filename
    session['file2_name'] = file2.filename
    return render_template('index.html', data=data, columns=columns, data2=data2, columns2=columns2)


#function compare 
@app.route('/compare', methods=['POST'])
def compare():
    keys1 = request.form.getlist('key1')
    keys2 = request.form.getlist('key2')

    try:
        df = pd.read_json(StringIO(session['data']))
        df2 = pd.read_json(StringIO(session['data2']))
    except Exception as e:
        flash(f"Erreur lors de la lecture des données en session : {e}", "error")
        return redirect(url_for('index'))

    if not keys1 or not keys2:
        flash("Veuillez sélectionner au moins une clé dans chaque fichier.", "error")
        return redirect(url_for('index'))
        
    if not all(k in df.columns for k in keys1) or not all(k in df2.columns for k in keys2):
        flash("Clés invalides sélectionnées.", "error")
        return redirect(url_for('index'))

    # Create concatenated keys for comparison
    df['_compare_key'] = df[keys1].astype(str).agg('|'.join, axis=1)
    df2['_compare_key'] = df2[keys2].astype(str).agg('|'.join, axis=1)

    file1_name = session.get('file1_name', 'Fichier 1')
    file2_name = session.get('file2_name', 'Fichier 2')

    merged = pd.merge(df, df2, left_on='_compare_key', right_on='_compare_key', how='outer', indicator=True)


    # Filter differences using indicator
    ecarts_fichier1 = merged[merged['_merge'] == 'left_only']
    ecarts_fichier2 = merged[merged['_merge'] == 'right_only']

    return render_template("compare.html",
                           key1=' + '.join(keys1),
                           key2=' + '.join(keys2),
                           ecarts1=ecarts_fichier1.to_dict(orient='records'),
                           ecarts2=ecarts_fichier2.to_dict(orient='records'),
                           file1_name=file1_name,
                           file2_name=file2_name)





if __name__ == '__main__':
    app.run(debug=True)
