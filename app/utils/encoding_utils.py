"""
Utilitaires pour la gestion des encodages de fichiers
"""
import pandas as pd


def detect_csv_encoding(file_path: str) -> str:
    """
    Détecte l'encodage d'un fichier CSV en testant plusieurs encodages courants
    
    Args:
        file_path: Chemin vers le fichier CSV
        
    Returns:
        str: L'encodage détecté
        
    Raises:
        ValueError: Si aucun encodage ne fonctionne
    """
    encodings_to_try = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings_to_try:
        try:
            # Test en lisant quelques lignes
            pd.read_csv(file_path, nrows=5, encoding=encoding)
            return encoding
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # Si ce n'est pas une erreur d'encodage, on continue d'essayer
            if "codec can't decode" not in str(e):
                continue
    
    raise ValueError(f"Impossible de détecter l'encodage du fichier {file_path}")


def safe_read_csv(file_path: str, **kwargs) -> pd.DataFrame:
    """
    Lecture sécurisée d'un fichier CSV avec détection automatique de l'encodage
    
    Args:
        file_path: Chemin vers le fichier CSV
        **kwargs: Arguments supplémentaires pour pd.read_csv
        
    Returns:
        pd.DataFrame: Le DataFrame lu
    """
    # Si l'encodage n'est pas spécifié, on le détecte
    if 'encoding' not in kwargs:
        encoding = detect_csv_encoding(file_path)
        kwargs['encoding'] = encoding
    
    return pd.read_csv(file_path, **kwargs)


def safe_read_file(file_path: str, **kwargs) -> pd.DataFrame:
    """
    Lecture sécurisée d'un fichier (CSV ou Excel) avec gestion automatique des encodages
    
    Args:
        file_path: Chemin vers le fichier
        **kwargs: Arguments supplémentaires pour les fonctions de lecture pandas
        
    Returns:
        pd.DataFrame: Le DataFrame lu
    """
    ext = file_path.split('.')[-1].lower()
    
    if ext == 'csv':
        return safe_read_csv(file_path, **kwargs)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file_path, **kwargs)
    elif ext == 'json':
        return pd.read_json(file_path, **kwargs)
    else:
        raise ValueError(f"Type de fichier non supporté: {ext}")
