import pandas as pd
import os
from typing import Iterator, Tuple, Optional

class LecteurFichierOptimise:
    """Optimized file reader for large files using chunking and memory-efficient operations"""
    
    def __init__(self, chunk_size: int = 5000):
        self.chunk_size = chunk_size
    
    def _detect_csv_delimiter(self, file_path: str, encoding: str = 'utf-8') -> str:
        """Detect CSV delimiter (comma, semicolon, tab, etc.)"""
        import csv
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Read a small sample
                sample = f.read(1024)
                
            # Use csv.Sniffer to detect delimiter
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            # Common delimiters to check if sniffer fails
            possible_delimiters = [',', ';', '\t', '|']
            
            # If sniffer found something not in our list, verify it
            if delimiter not in possible_delimiters:
                # Count occurrences of each delimiter in the sample
                delimiter_counts = {}
                for delim in possible_delimiters:
                    delimiter_counts[delim] = sample.count(delim)
                
                # Choose the most frequent one
                delimiter = max(delimiter_counts, key=delimiter_counts.get)
            
            return delimiter
            
        except Exception:
            # Default fallback
            return ','
    
    def read_file_info(self, file_path: str) -> dict:
        """Get basic file information without loading entire file"""
        ext = file_path.split('.')[-1].lower()
        
        if ext == 'csv':
            # Try multiple encodings with robust parameters
            encodings_to_try = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1', 'cp1252']
            sample_df = None
            used_encoding = None
            used_delimiter = None
            
            for encoding in encodings_to_try:
                try:
                    # Detect delimiter first
                    delimiter = self._detect_csv_delimiter(file_path, encoding)
                    used_delimiter = delimiter
                    
                    sample_df = pd.read_csv(file_path, nrows=5, encoding=encoding,
                                          delimiter=delimiter, on_bad_lines='skip', engine='python')
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    if "codec can't decode" not in str(e) and "tokenizing data" not in str(e):
                        continue
            
            if sample_df is None:
                raise ValueError("Impossible de lire le fichier avec les encodages supportés (utf-8, latin-1, windows-1252)")
            
            # Get total row count efficiently with the same encoding and delimiter
            try:
                with open(file_path, 'r', encoding=used_encoding) as f:
                    row_count = sum(1 for line in f) - 1  # Subtract header
            except Exception:
                # Fallback: read the file and count rows
                temp_df = pd.read_csv(file_path, encoding=used_encoding, delimiter=used_delimiter,
                                    on_bad_lines='skip', engine='python')
                row_count = len(temp_df)
                
        elif ext in ['xls', 'xlsx']:
            # For Excel, read small sample first
            sample_df = pd.read_excel(file_path, nrows=5)
            # Get total rows (this is less efficient for Excel, but necessary)
            full_df = pd.read_excel(file_path, usecols=[0])  # Just first column
            row_count = len(full_df)
        else:
            raise ValueError(f"Type de fichier non supporté: {ext}")
        
        return {
            'columns': sample_df.columns.tolist(),
            'total_rows': row_count,
            'total_columns': len(sample_df.columns),
            'sample_data': sample_df.to_dict(orient='records'),
            'file_extension': ext,
            'encoding': used_encoding if ext == 'csv' else None,
            'delimiter': used_delimiter if ext == 'csv' else None
        }
    
    def read_file_chunks(self, file_path: str, encoding: str = None) -> Iterator[pd.DataFrame]:
        """Read file in chunks to manage memory usage"""
        ext = file_path.split('.')[-1].lower()
        
        if ext == 'csv':
            # Determine encoding if not provided
            if encoding is None:
                encodings_to_try = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1', 'cp1252']
                for enc in encodings_to_try:
                    try:
                        # Test with first few rows
                        pd.read_csv(file_path, nrows=5, encoding=enc,
                                  on_bad_lines='skip', engine='python')
                        encoding = enc
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception:
                        continue
                
                if encoding is None:
                    encoding = 'utf-8'  # Fallback
            
            chunk_iter = pd.read_csv(file_path, chunksize=self.chunk_size, encoding=encoding,
                                   on_bad_lines='skip', engine='python')
            for chunk in chunk_iter:
                yield chunk
        elif ext in ['xls', 'xlsx']:
            # Excel doesn't support native chunking, so we read and split
            df = pd.read_excel(file_path)
            for i in range(0, len(df), self.chunk_size):
                yield df.iloc[i:i + self.chunk_size]
        else:
            raise ValueError(f"Type de fichier non supporté: {ext}")
    
    def create_key_index(self, file_path: str, key_columns: list) -> dict:
        """Create an index of keys for efficient comparison"""
        key_index = {}
        
        for chunk_idx, chunk in enumerate(self.read_file_chunks(file_path)):
            # Create composite key
            chunk['_key'] = chunk[key_columns].astype(str).agg('|'.join, axis=1)
            
            # Store key -> (chunk_index, row_index) mapping
            for row_idx, key in enumerate(chunk['_key']):
                if key in key_index:
                    # Handle duplicates
                    if not isinstance(key_index[key], list):
                        key_index[key] = [key_index[key]]
                    key_index[key].append((chunk_idx, row_idx))
                else:
                    key_index[key] = (chunk_idx, row_idx)
        
        return key_index
    
    def get_file_sample(self, file_path: str, sample_size: int = 1000) -> pd.DataFrame:
        """Get a representative sample of the file for quick preview"""
        ext = file_path.split('.')[-1].lower()
        
        if ext == 'csv':
            # Get file info including encoding
            file_info = self.read_file_info(file_path)
            encoding = file_info.get('encoding', 'utf-8')
            total_rows = file_info['total_rows']
            
            if total_rows <= sample_size:
                return pd.read_csv(file_path, encoding=encoding,
                                 on_bad_lines='skip', engine='python')
            
            # Use nrows to limit the number of rows read
            return pd.read_csv(file_path, nrows=sample_size, encoding=encoding,
                             on_bad_lines='skip', engine='python')
        
        elif ext in ['xls', 'xlsx']:
            return pd.read_excel(file_path, nrows=sample_size)
        
        else:
            raise ValueError(f"Type de fichier non supporté: {ext}")

def read_uploaded_file_optimized(file_storage, max_preview_rows: int = 1000):
    """Optimized version of file reading that handles large files efficiently"""
    # Save file temporarily
    temp_path = f"temp/{file_storage.filename}"
    os.makedirs("temp", exist_ok=True)
    file_storage.save(temp_path)
    
    try:
        lecteur = LecteurFichierOptimise()
        
        # Get file info first
        file_info = lecteur.read_file_info(temp_path)
        
        # If file is small enough, read normally
        if file_info['total_rows'] <= 10000 and file_info['total_columns'] <= 50:
            ext = file_info['file_extension']
            if ext == 'csv':
                encoding = file_info.get('encoding', 'utf-8')
                delimiter = file_info.get('delimiter', ',')
                df = pd.read_csv(temp_path, encoding=encoding, delimiter=delimiter,
                               on_bad_lines='skip', engine='python')
            elif ext in ['xls', 'xlsx']:
                df = pd.read_excel(temp_path)
            
            return {
                'data': df,
                'is_large_file': False,
                'file_info': file_info,
                'temp_path': temp_path
            }
        
        # For large files, return sample and file info
        sample_df = lecteur.get_file_sample(temp_path, max_preview_rows)
        
        return {
            'data': sample_df,
            'is_large_file': True,
            'file_info': file_info,
            'temp_path': temp_path
        }
    
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e
