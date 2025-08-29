import pandas as pd
from app.utils.encoding_utils import safe_read_csv
import tempfile
import os

def read_uploaded_file(file_storage):
    """Read uploaded file and return DataFrame based on file extension"""
    ext = file_storage.filename.split('.')[-1].lower()
    
    if ext == 'csv':
        # Save to temporary file to use safe_read_csv
        temp_path = f"temp/{file_storage.filename}"
        os.makedirs("temp", exist_ok=True)
        file_storage.save(temp_path)
        
        try:
            return safe_read_csv(temp_path)
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file_storage)
    elif ext == 'json':
        return pd.read_json(file_storage)
    else:
        raise ValueError("Type de fichier non supporté")
