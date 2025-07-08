from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = '12GQSGQza&ç_çàFAFSF'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

    return render_template('index.html', data=data, columns=columns, data2=data2, columns2=columns2)

if __name__ == '__main__':
    app.run(debug=True)
