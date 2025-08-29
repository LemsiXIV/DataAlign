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
            # Test en lisant quelques lignes avec paramètres robustes
            pd.read_csv(file_path, nrows=5, encoding=encoding, 
                       on_bad_lines='skip', engine='python')
            return encoding
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # Si ce n'est pas une erreur d'encodage, on continue d'essayer
            if "codec can't decode" not in str(e) and "tokenizing data" not in str(e):
                continue
    
    raise ValueError(f"Impossible de détecter l'encodage du fichier {file_path}")


def safe_read_csv(file_path: str, **kwargs) -> pd.DataFrame:
    """
    Lecture sécurisée d'un fichier CSV avec détection automatique de l'encodage
    et gestion des erreurs de parsing
    
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
    
    # Paramètres pour une lecture plus robuste
    safe_params = {
        'encoding': kwargs.get('encoding', 'utf-8'),
        'on_bad_lines': 'skip',  # Ignorer les lignes malformées
        'engine': 'python',     # Utiliser le parser Python (plus flexible)
        'quoting': 1,           # QUOTE_ALL - traiter les guillemets
        'skipinitialspace': True,  # Ignorer les espaces après les délimiteurs
        'dtype': str,           # Lire toutes les colonnes comme string pour éviter les erreurs de type
    }
    
    # Fusionner avec les paramètres fournis
    final_params = {**safe_params, **kwargs}
    
    try:
        # Première tentative avec les paramètres sécurisés
        return pd.read_csv(file_path, **final_params)
    except Exception as e:
        print(f"Première tentative échouée: {e}")
        
        # Deuxième tentative : essayer différents séparateurs
        separators = [',', ';', '\t', '|']
        for sep in separators:
            try:
                test_params = final_params.copy()
                test_params['sep'] = sep
                df = pd.read_csv(file_path, **test_params)
                if len(df.columns) > 1:  # Vérifier qu'on a bien plusieurs colonnes
                    print(f"Lecture réussie avec le séparateur: '{sep}'")
                    return df
            except Exception:
                continue
        
        # Troisième tentative : mode très permissif
        try:
            permissive_params = {
                'encoding': final_params['encoding'],
                'on_bad_lines': 'skip',
                'engine': 'python',
                'sep': None,  # Laisser pandas deviner le séparateur
                'header': 'infer',
                'dtype': str,
                'error_bad_lines': False,  # Pour compatibilité
                'warn_bad_lines': False
            }
            
            df = pd.read_csv(file_path, **permissive_params)
            print(f"Lecture réussie en mode permissif")
            return df
        except Exception as e2:
            print(f"Mode permissif échoué: {e2}")
            
            # Dernière tentative : lecture ligne par ligne pour identifier le problème
            try:
                return _read_csv_line_by_line(file_path, final_params['encoding'])
            except Exception as e3:
                raise ValueError(f"Impossible de lire le fichier CSV {file_path}. Erreurs: {str(e)}, {str(e2)}, {str(e3)}")


def _read_csv_line_by_line(file_path: str, encoding: str) -> pd.DataFrame:
    """
    Lecture CSV ligne par ligne pour identifier et corriger les problèmes
    """
    import csv
    
    rows = []
    headers = None
    expected_cols = None
    
    with open(file_path, 'r', encoding=encoding) as f:
        # Détecter le dialecte CSV
        sample = f.read(1024)
        f.seek(0)
        
        try:
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.reader(f, dialect)
        except:
            # Fallback vers le reader par défaut
            reader = csv.reader(f)
        
        for line_num, row in enumerate(reader, 1):
            if line_num == 1:
                headers = row
                expected_cols = len(headers)
                rows.append(row)
            else:
                # Vérifier le nombre de colonnes
                if len(row) == expected_cols:
                    rows.append(row)
                elif len(row) > expected_cols:
                    # Tronquer les colonnes en trop
                    print(f"Ligne {line_num}: {len(row)} colonnes au lieu de {expected_cols}, troncature appliquée")
                    rows.append(row[:expected_cols])
                elif len(row) < expected_cols:
                    # Compléter avec des valeurs vides
                    print(f"Ligne {line_num}: {len(row)} colonnes au lieu de {expected_cols}, complétée avec des valeurs vides")
                    padded_row = row + [''] * (expected_cols - len(row))
                    rows.append(padded_row)
    
    if not rows:
        raise ValueError("Fichier CSV vide ou illisible")
    
    df = pd.DataFrame(rows[1:], columns=rows[0])
    print(f"Lecture ligne par ligne réussie: {len(df)} lignes, {len(df.columns)} colonnes")
    return df


def safe_read_file(file_path: str, **kwargs) -> pd.DataFrame:
    """
    Lecture sécurisée d'un fichier (CSV ou Excel) avec gestion automatique des encodages
    et des erreurs de parsing
    
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
        try:
            return pd.read_excel(file_path, **kwargs)
        except Exception as e:
            print(f"Erreur lors de la lecture Excel: {e}")
            # Essayer avec différents engines
            engines = ['openpyxl', 'xlrd']
            for engine in engines:
                try:
                    return pd.read_excel(file_path, engine=engine, **kwargs)
                except Exception:
                    continue
            raise e
    elif ext == 'json':
        return pd.read_json(file_path, **kwargs)
    else:
        raise ValueError(f"Type de fichier non supporté: {ext}")
