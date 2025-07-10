from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, make_response
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO 
import json
import os
import io
import pdfkit
import tempfile
app = Flask(__name__)
app.secret_key = '12GQSGQza&ç_çàFAFSF'



UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
@app.route("/index")
def index():
    image_url = 'sofrecom.svg'
    return render_template("index.html",image_url=image_url)

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

    # Filter pour communs ligne
    communs = merged[merged['_merge'] == 'both']

    # Donner pour la chart Pi Pourcentage
    total = len(merged)
    pct1 = round(len(ecarts_fichier1) / total * 100, 2)
    pct2 = round(len(ecarts_fichier2) / total * 100, 2)
    pct_both = round(len(communs) / total * 100, 2)

    # totaux bruts 
    n1 = len(ecarts_fichier1)
    n2 = len(ecarts_fichier2)
    n_common = len(communs)
    total_ecarts = n1 + n2
    nb_df = len(df)
    nb_df2 = len(df2)


    return render_template("compare.html",
                           key1=' + '.join(keys1),
                           key2=' + '.join(keys2),
                           ecarts1=ecarts_fichier1.to_dict(orient='records'),
                           ecarts2=ecarts_fichier2.to_dict(orient='records'),
                           file1_name=file1_name,
                           file2_name=file2_name,
                           pct1=pct1,
                           pct2=pct2,
                           pct_both=pct_both,
                           n1=n1,
                           n2=n2,
                           n_common=n_common,
                           total=total,
                           total_ecarts=total_ecarts,
                           nb_df=nb_df,
                           nb_df2=nb_df2)

# Function Download d'un fichier xlsx 
@app.route('/download')
def download_excel():
    try:
        df = pd.read_json(StringIO(session['data']))
        df2 = pd.read_json(StringIO(session['data2']))
    except Exception as e:
        flash(f"Erreur lors du chargement des données pour export : {e}", "error")
        return redirect(url_for('index'))

    keys1 = request.args.getlist('key1')
    keys2 = request.args.getlist('key2')

    if not keys1 or not keys2:
        flash("Clés manquantes pour la génération du fichier", "error")
        return redirect(url_for('index'))

    df['_compare_key'] = df[keys1].astype(str).agg('|'.join, axis=1)
    df2['_compare_key'] = df2[keys2].astype(str).agg('|'.join, axis=1)

    merged = pd.merge(df, df2, on='_compare_key', how='outer', indicator=True)

    only1 = merged[merged['_merge'] == 'left_only'].drop(columns=['_compare_key', '_merge'])
    only2 = merged[merged['_merge'] == 'right_only'].drop(columns=['_compare_key', '_merge'])
    both = merged[merged['_merge'] == 'both'].drop(columns=['_compare_key', '_merge'])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'middle',
            'fg_color': '#D7E4BC',
            'border': 1
        })

        def write_sheet(df, sheet_name):
            df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=3)
            worksheet = writer.sheets[sheet_name]
            worksheet.insert_image('L2', 'static/sofrecom.png', {'x_scale': 0.5, 'y_scale': 0.5})
            worksheet.write('C1', f"Rapport de comparaison – {sheet_name}", workbook.add_format({'bold': True, 'font_size': 14}))
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(3, col_num, value, header_format)

        write_sheet(only1, "Ecarts Fichier 1")
        write_sheet(only2, "Ecarts Fichier 2")
        write_sheet(both, "Communs")

    output.seek(0)
    return send_file(output,
                     download_name="rapport_comparaison.xlsx",
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Function Download d'un Rapport PDF
@app.route('/download_pdf')
def download_pdf():
    try:
        df = pd.read_json(StringIO(session['data']))
        df2 = pd.read_json(StringIO(session['data2']))
    except Exception as e:
        flash(f"Erreur : {e}", "error")
        return redirect(url_for('index'))

    keys1 = request.args.getlist('key1')
    keys2 = request.args.getlist('key2')

    df['_compare_key'] = df[keys1].astype(str).agg('|'.join, axis=1)
    df2['_compare_key'] = df2[keys2].astype(str).agg('|'.join, axis=1)

    merged = pd.merge(df, df2, on='_compare_key', how='outer', indicator=True)
    ecarts1 = merged[merged['_merge'] == 'left_only'].drop(columns=['_compare_key', '_merge']).to_dict(orient='records')
    ecarts2 = merged[merged['_merge'] == 'right_only'].drop(columns=['_compare_key', '_merge']).to_dict(orient='records')

    total1 = len(df)
    total2 = len(df2)
    communes = len(merged[merged['_merge'] == 'both'])
    only1 = len(ecarts1)
    only2 = len(ecarts2)

    labels = [f'{session.get("file1_name")} seulement', 
              f'{session.get("file2_name")} seulement', 
              'Communs']
    sizes = [only1, only2, communes]
    colors = ['#FF9999', '#66B3FF', '#99FF99']

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
    plt.axis('equal')
    chart_path = os.path.join('static', 'pie_chart.png')
    plt.savefig(chart_path, bbox_inches='tight')
    plt.close()

    # Get absolute paths for images for wkhtmltopdf
    logo_path_abs = os.path.abspath(os.path.join('static', 'sofrecom.png'))
    chart_path_abs = os.path.abspath(chart_path)

    rendered_html = render_template('report.html',
    file1_name=session.get('file1_name'),
    file2_name=session.get('file2_name'),
    ecarts1=ecarts1,
    ecarts2=ecarts2,
    total1=total1,
    total2=total2,
    lignes_communes=communes,
    logo_path='file:///' + logo_path_abs.replace('\\', '/'),
    chart_path='file:///' + chart_path_abs.replace('\\', '/')
)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
        f.write(rendered_html.encode('utf-8'))
        temp_html_path = f.name

    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

    try:
        #allow acces to the path with options
        options = { 'enable-local-file-access': '' }
        pdf = pdfkit.from_file(temp_html_path, False, configuration=config, options=options)

    except Exception as e:
        flash(f"Erreur lors de la génération du PDF : {e}", "error")
        return redirect(url_for('index'))

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=rapport_comparaison.pdf'

    #Debug si l'image est d'un path vvalide ou pas 
    print("LOGO PATH:", logo_path_abs)
    print("CHART PATH:", chart_path_abs)
    print("Exists?", os.path.exists(logo_path_abs), os.path.exists(chart_path_abs))


    # Clean up temp file
    os.remove(temp_html_path)

    return response

if __name__ == '__main__':
    app.run(debug=True)
