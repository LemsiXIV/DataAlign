import matplotlib.pyplot as plt
import os
import tempfile
import pdfkit
from flask import render_template, make_response

class GenerateurPdf:
    def __init__(self, ecarts1, ecarts2, file1_name, file2_name, total1, total2, communes, project_folder=None):
        self.ecarts1 = ecarts1
        self.ecarts2 = ecarts2
        self.file1_name = file1_name
        self.file2_name = file2_name
        self.total1 = total1
        self.total2 = total2
        self.communes = communes
        self.project_folder = project_folder
        
    def generer_graphique(self):
        """Generate pie chart for PDF report"""
        only1 = len(self.ecarts1)
        only2 = len(self.ecarts2)
        
        labels = [f'{self.file1_name} seulement', 
                  f'{self.file2_name} seulement', 
                  'Communs']
        sizes = [only1, only2, self.communes]
        colors = ['#FF9999', '#66B3FF', '#99FF99']

        plt.figure(figsize=(6, 6))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
        plt.axis('equal')
        
        # Sauvegarder dans le dossier static pour l'affichage
        chart_path = os.path.join('app/static', 'pie_chart.png')
        plt.savefig(chart_path, bbox_inches='tight')
        
        # Sauvegarder aussi dans le dossier du projet si disponible
        if self.project_folder and os.path.exists(self.project_folder):
            project_chart_path = os.path.join(self.project_folder, 'pie_chart.png')
            plt.savefig(project_chart_path, bbox_inches='tight')
        
        plt.close()
        
        return chart_path
        
    def generer_pdf(self):
        """Generate PDF report"""
        chart_path = self.generer_graphique()
        
        # Get absolute paths for images for wkhtmltopdf
        logo_path_abs = os.path.abspath(os.path.join('app/static', 'sofrecom.png'))
        chart_path_abs = os.path.abspath(chart_path)

        # Convert DataFrames to dict and handle empty cases
        ecarts1_records = self.ecarts1.to_dict(orient='records') if not self.ecarts1.empty else []
        ecarts2_records = self.ecarts2.to_dict(orient='records') if not self.ecarts2.empty else []
        
        # Get column names safely
        ecarts1_columns = list(self.ecarts1.columns) if not self.ecarts1.empty else []
        ecarts2_columns = list(self.ecarts2.columns) if not self.ecarts2.empty else []

        rendered_html = render_template('report.html',
            file1_name=self.file1_name,
            file2_name=self.file2_name,
            ecarts1=ecarts1_records,
            ecarts2=ecarts2_records,
            ecarts1_columns=ecarts1_columns,
            ecarts2_columns=ecarts2_columns,
            total1=self.total1,
            total2=self.total2,
            lignes_communes=self.communes,
            logo_path='file:///' + logo_path_abs.replace('\\', '/'),
            chart_path='file:///' + chart_path_abs.replace('\\', '/')
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            f.write(rendered_html.encode('utf-8'))
            temp_html_path = f.name

        config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

        try:
            options = { 'enable-local-file-access': '' }
            pdf = pdfkit.from_file(temp_html_path, False, configuration=config, options=options)
        except Exception as e:
            raise Exception(f"Erreur lors de la génération du PDF : {e}")

        # Save to project folder if specified
        if self.project_folder:
            pdf_path = os.path.join(self.project_folder, "rapport_comparaison.pdf")
            os.makedirs(self.project_folder, exist_ok=True)
            with open(pdf_path, 'wb') as f:
                f.write(pdf)

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=rapport_comparaison.pdf'

        # Clean up temp file
        os.remove(temp_html_path)

        return response
    
    def generer_pdf_fichier(self, file_path):
        """Generate PDF report and save to specified file path"""
        chart_path = self.generer_graphique()
        
        # Get absolute paths for images for wkhtmltopdf
        logo_path_abs = os.path.abspath(os.path.join('app/static', 'sofrecom.png'))
        chart_path_abs = os.path.abspath(chart_path)

        # Convert DataFrames to dict and handle empty cases
        ecarts1_records = self.ecarts1.to_dict(orient='records') if not self.ecarts1.empty else []
        ecarts2_records = self.ecarts2.to_dict(orient='records') if not self.ecarts2.empty else []
        
        # Get column names safely
        ecarts1_columns = list(self.ecarts1.columns) if not self.ecarts1.empty else []
        ecarts2_columns = list(self.ecarts2.columns) if not self.ecarts2.empty else []

        rendered_html = render_template('report.html',
            file1_name=self.file1_name,
            file2_name=self.file2_name,
            ecarts1=ecarts1_records,
            ecarts2=ecarts2_records,
            ecarts1_columns=ecarts1_columns,
            ecarts2_columns=ecarts2_columns,
            total1=self.total1,
            total2=self.total2,
            lignes_communes=self.communes,
            logo_path='file:///' + logo_path_abs.replace('\\', '/'),
            chart_path='file:///' + chart_path_abs.replace('\\', '/')
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            f.write(rendered_html.encode('utf-8'))
            temp_html_path = f.name

        config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

        try:
            options = { 'enable-local-file-access': '' }
            pdf = pdfkit.from_file(temp_html_path, False, configuration=config, options=options)
        except Exception as e:
            raise Exception(f"Erreur lors de la génération du PDF : {e}")

        # Save PDF to specified file path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(pdf)

        # Clean up temp file
        os.remove(temp_html_path)
