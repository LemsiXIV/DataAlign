import pandas as pd

def read_uploaded_file(file_storage):
    """Read uploaded file and return DataFrame based on file extension"""
    ext = file_storage.filename.split('.')[-1].lower()
    if ext == 'csv':
        return pd.read_csv(file_storage)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file_storage)
    elif ext == 'json':
        return pd.read_json(file_storage)
    else:
        raise ValueError("Type de fichier non supporté")
