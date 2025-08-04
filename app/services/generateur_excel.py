import pandas as pd
import io
import os
from flask import send_file

class GenerateurExcel:
    def __init__(self, ecarts1, ecarts2, communs, project_folder=None):
        self.ecarts1 = ecarts1
        self.ecarts2 = ecarts2
        self.communs = communs
        self.project_folder = project_folder
        
    def generer_rapport(self):
        """Generate Excel report with comparison results"""
        only1 = self.ecarts1.drop(columns=['_compare_key', '_merge'], errors='ignore')
        only2 = self.ecarts2.drop(columns=['_compare_key', '_merge'], errors='ignore')
        both = self.communs.drop(columns=['_compare_key', '_merge'], errors='ignore')

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
                worksheet.insert_image('N1', 'app/static/sofrecom.png', {'x_scale': 0.5, 'y_scale': 0.5})
                worksheet.write('C1', f"Rapport de comparaison – {sheet_name}", workbook.add_format({'bold': True, 'font_size': 14}))
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(3, col_num, value, header_format)

            write_sheet(only1, "Ecarts Fichier 1")
            write_sheet(only2, "Ecarts Fichier 2")
            write_sheet(both, "Communs")

        output.seek(0)
        
        # Save to project folder if specified
        if self.project_folder:
            excel_path = os.path.join(self.project_folder, "rapport_comparaison.xlsx")
            os.makedirs(self.project_folder, exist_ok=True)
            with open(excel_path, 'wb') as f:
                f.write(output.getvalue())
        
        return send_file(output,
                        download_name="rapport_comparaison.xlsx",
                        as_attachment=True,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    def generer_rapport_fichier(self, file_path):
        """Generate Excel report and save to specified file path"""
        only1 = self.ecarts1.drop(columns=['_compare_key', '_merge'], errors='ignore')
        only2 = self.ecarts2.drop(columns=['_compare_key', '_merge'], errors='ignore')
        both = self.communs.drop(columns=['_compare_key', '_merge'], errors='ignore')

        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
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
                worksheet.insert_image('N1', 'app/static/sofrecom.png', {'x_scale': 0.5, 'y_scale': 0.5})
                worksheet.write('C1', f"Rapport de comparaison – {sheet_name}", workbook.add_format({'bold': True, 'font_size': 14}))
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(3, col_num, value, header_format)

            write_sheet(only1, "Ecarts Fichier 1")
            write_sheet(only2, "Ecarts Fichier 2")
            write_sheet(both, "Communs")
