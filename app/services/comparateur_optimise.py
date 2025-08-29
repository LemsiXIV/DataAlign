import pandas as pd
import os
import sqlite3
from typing import Dict, List, Tuple, Iterator
import tempfile
import json
from datetime import datetime
from .memory_manager import MemoryManager, ChunkProcessor
from app.utils.encoding_utils import safe_read_csv, detect_csv_encoding

class ComparateurFichiersOptimise:
    """Optimized file comparator for large files using chunking and database operations"""
    
    def __init__(self, file1_path: str, file2_path: str, keys1: List[str], keys2: List[str], 
                 chunk_size: int = 5000, use_sqlite: bool = True):
        self.file1_path = file1_path
        self.file2_path = file2_path
        self.keys1 = keys1
        self.keys2 = keys2
        self.chunk_size = chunk_size
        self.use_sqlite = use_sqlite
        self.memory_manager = MemoryManager()
        self.chunk_processor = ChunkProcessor(chunk_size)
        
        # Auto-detect if chunking should be used based on file sizes
        if use_sqlite:
            try:
                from .lecteur_fichier_optimise import LecteurFichierOptimise
                lecteur = LecteurFichierOptimise()
                file1_info = lecteur.read_file_info(file1_path)
                file2_info = lecteur.read_file_info(file2_path)
                
                # Adjust chunk size based on available memory
                available_memory = self.memory_manager.get_memory_usage()['available_mb']
                optimal_chunk = self.chunk_processor.adaptive_chunk_size(
                    file1_info['total_rows'] + file2_info['total_rows'], 
                    available_memory
                )
                self.chunk_size = optimal_chunk
                
                print(f"File 1: {file1_info['total_rows']} rows, {file1_info['total_columns']} columns")
                print(f"File 2: {file2_info['total_rows']} rows, {file2_info['total_columns']} columns")
                print(f"Using chunk size: {self.chunk_size}")
                
            except Exception as e:
                print(f"Could not analyze files for optimization: {e}")
        
        # Create temporary database for large file operations
        if self.use_sqlite:
            self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
            self.db_path = self.temp_db.name
            self.temp_db.close()
            self.conn = sqlite3.connect(self.db_path)
            self._setup_database()
    
    def _setup_database(self):
        """Setup temporary SQLite database for efficient operations"""
        cursor = self.conn.cursor()
        
        # Create tables for file data
        cursor.execute('''
            CREATE TABLE file1_data (
                id INTEGER PRIMARY KEY,
                composite_key TEXT,
                row_data TEXT,
                UNIQUE(composite_key)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE file2_data (
                id INTEGER PRIMARY KEY,
                composite_key TEXT,
                row_data TEXT,
                UNIQUE(composite_key)
            )
        ''')
        
        # Create indexes for fast lookups
        cursor.execute('CREATE INDEX idx_file1_key ON file1_data(composite_key)')
        cursor.execute('CREATE INDEX idx_file2_key ON file2_data(composite_key)')
        
        self.conn.commit()
    
    def _read_file_chunks(self, file_path: str) -> Iterator[pd.DataFrame]:
        """Read file in chunks"""
        ext = file_path.split('.')[-1].lower()
        
        if ext == 'csv':
            encoding = detect_csv_encoding(file_path)
            chunk_iter = pd.read_csv(file_path, chunksize=self.chunk_size, encoding=encoding)
            for chunk in chunk_iter:
                yield chunk
        elif ext in ['xls', 'xlsx']:
            df = pd.read_excel(file_path)
            for i in range(0, len(df), self.chunk_size):
                yield df.iloc[i:i + self.chunk_size]
        else:
            raise ValueError(f"Type de fichier non supporté: {ext}")
    
    def _create_composite_key(self, row: pd.Series, key_columns: List[str]) -> str:
        """Create composite key from specified columns"""
        return '|'.join(str(row[col]) for col in key_columns)
    
    def _load_file_to_db(self, file_path: str, table_name: str, key_columns: List[str]):
        """Load file data into SQLite database in chunks with memory monitoring"""
        cursor = self.conn.cursor()
        processed_rows = 0
        
        print(f"Loading {file_path} into database...")
        
        for chunk_idx, chunk in enumerate(self._read_file_chunks(file_path)):
            # Monitor memory usage
            if chunk_idx % 10 == 0:  # Check every 10 chunks
                memory_info = self.memory_manager.get_memory_usage()
                print(f"Processed {processed_rows} rows, Memory: {memory_info['rss_mb']:.1f} MB")
                
                # Force garbage collection if memory usage is high
                if memory_info['percent'] > 75:
                    self.memory_manager.force_garbage_collection()
            
            # Optimize chunk memory usage
            chunk = self.memory_manager.optimize_dataframe_memory(chunk)
            
            batch_data = []
            for _, row in chunk.iterrows():
                composite_key = self._create_composite_key(row, key_columns)
                row_data = row.to_json()
                batch_data.append((composite_key, row_data))
            
            # Insert batch data with IGNORE to handle duplicates
            cursor.executemany(
                f'INSERT OR IGNORE INTO {table_name} (composite_key, row_data) VALUES (?, ?)',
                batch_data
            )
            
            processed_rows += len(chunk)
            
            # Commit periodically to avoid large transaction logs
            if chunk_idx % 20 == 0:
                self.conn.commit()
        
        # Final commit
        self.conn.commit()
        print(f"Finished loading {processed_rows} rows into {table_name}")
        
        # Final garbage collection
        self.memory_manager.force_garbage_collection()
    
    def _get_comparison_results_db(self) -> Dict:
        """Get comparison results using database operations"""
        cursor = self.conn.cursor()
        
        # Count statistics
        cursor.execute('SELECT COUNT(*) FROM file1_data')
        total_file1 = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM file2_data')
        total_file2 = cursor.fetchone()[0]
        
        # Find common keys
        cursor.execute('''
            SELECT COUNT(*) FROM file1_data f1
            INNER JOIN file2_data f2 ON f1.composite_key = f2.composite_key
        ''')
        n_common = cursor.fetchone()[0]
        
        # Find keys only in file1
        cursor.execute('''
            SELECT COUNT(*) FROM file1_data f1
            LEFT JOIN file2_data f2 ON f1.composite_key = f2.composite_key
            WHERE f2.composite_key IS NULL
        ''')
        n1 = cursor.fetchone()[0]
        
        # Find keys only in file2
        cursor.execute('''
            SELECT COUNT(*) FROM file2_data f2
            LEFT JOIN file1_data f1 ON f2.composite_key = f1.composite_key
            WHERE f1.composite_key IS NULL
        ''')
        n2 = cursor.fetchone()[0]
        
        total = n1 + n2 + n_common
        
        return {
            'n1': n1,
            'n2': n2,
            'n_common': n_common,
            'total': total,
            'nb_df': total_file1,
            'nb_df2': total_file2,
            'total_ecarts': n1 + n2,
            'pct1': round(n1 / total * 100, 2) if total > 0 else 0,
            'pct2': round(n2 / total * 100, 2) if total > 0 else 0,
            'pct_both': round(n_common / total * 100, 2) if total > 0 else 0
        }
    
    def _get_difference_data_db(self, limit: int = 1000) -> Dict:
        """Get sample of difference data from database"""
        cursor = self.conn.cursor()
        
        # Get sample of records only in file1
        cursor.execute('''
            SELECT f1.row_data FROM file1_data f1
            LEFT JOIN file2_data f2 ON f1.composite_key = f2.composite_key
            WHERE f2.composite_key IS NULL
            LIMIT ?
        ''', (limit,))
        
        ecarts_file1_data = []
        for row in cursor.fetchall():
            ecarts_file1_data.append(json.loads(row[0]))
        
        # Get sample of records only in file2
        cursor.execute('''
            SELECT f2.row_data FROM file2_data f2
            LEFT JOIN file1_data f1 ON f2.composite_key = f1.composite_key
            WHERE f1.composite_key IS NULL
            LIMIT ?
        ''', (limit,))
        
        ecarts_file2_data = []
        for row in cursor.fetchall():
            ecarts_file2_data.append(json.loads(row[0]))
        
        # Get sample of common records
        cursor.execute('''
            SELECT f1.row_data FROM file1_data f1
            INNER JOIN file2_data f2 ON f1.composite_key = f2.composite_key
            LIMIT ?
        ''', (limit,))
        
        communs_data = []
        for row in cursor.fetchall():
            communs_data.append(json.loads(row[0]))
        
        return {
            'ecarts_fichier1': pd.DataFrame(ecarts_file1_data),
            'ecarts_fichier2': pd.DataFrame(ecarts_file2_data),
            'communs': pd.DataFrame(communs_data)
        }
    
    def comparer_optimise(self, sample_size: int = 1000) -> Dict:
        """Optimized comparison method for large files with memory management"""
        def _perform_comparison():
            if self.use_sqlite:
                # Load data into database with memory monitoring
                print("Starting optimized comparison with database backend...")
                self._load_file_to_db(self.file1_path, 'file1_data', self.keys1)
                self._load_file_to_db(self.file2_path, 'file2_data', self.keys2)
                
                print("Computing comparison statistics...")
                # Get statistics
                stats = self._get_comparison_results_db()
                
                print("Getting sample data...")
                # Get sample data for display
                sample_data = self._get_difference_data_db(sample_size)
                
                # Combine results
                return {**stats, **sample_data}
                
            else:
                # Fallback to in-memory comparison for smaller files
                return self._comparer_in_memory()
        
        try:
            # Use memory monitoring wrapper
            return self.chunk_processor.process_with_memory_monitoring(_perform_comparison)
            
        except Exception as e:
            print(f"Error during comparison: {e}")
            raise e
    
    def _comparer_in_memory(self) -> Dict:
        """Fallback in-memory comparison for smaller files"""
        # Read files completely
        ext1 = self.file1_path.split('.')[-1].lower()
        ext2 = self.file2_path.split('.')[-1].lower()
        
        if ext1 == 'csv':
            df1 = safe_read_csv(self.file1_path)
        elif ext1 in ['xls', 'xlsx']:
            df1 = pd.read_excel(self.file1_path)
        
        if ext2 == 'csv':
            df2 = safe_read_csv(self.file2_path)
        elif ext2 in ['xls', 'xlsx']:
            df2 = pd.read_excel(self.file2_path)
        
        # Create composite keys
        df1['_compare_key'] = df1[self.keys1].astype(str).agg('|'.join, axis=1)
        df2['_compare_key'] = df2[self.keys2].astype(str).agg('|'.join, axis=1)
        
        # Merge and compare
        merged = pd.merge(df1, df2, on='_compare_key', how='outer', indicator=True)
        
        ecarts_fichier1 = merged[merged['_merge'] == 'left_only']
        ecarts_fichier2 = merged[merged['_merge'] == 'right_only']
        communs = merged[merged['_merge'] == 'both']
        
        total = len(merged)
        n1 = len(ecarts_fichier1)
        n2 = len(ecarts_fichier2)
        n_common = len(communs)
        
        return {
            'ecarts_fichier1': ecarts_fichier1,
            'ecarts_fichier2': ecarts_fichier2,
            'communs': communs,
            'total': total,
            'n1': n1,
            'n2': n2,
            'n_common': n_common,
            'total_ecarts': n1 + n2,
            'nb_df': len(df1),
            'nb_df2': len(df2),
            'pct1': round(n1 / total * 100, 2) if total > 0 else 0,
            'pct2': round(n2 / total * 100, 2) if total > 0 else 0,
            'pct_both': round(n_common / total * 100, 2) if total > 0 else 0
        }
    
    def cleanup(self):
        """Clean up temporary resources"""
        if self.use_sqlite and hasattr(self, 'conn'):
            self.conn.close()
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Compatibility function for existing code
def compare_large_files(file1_path: str, file2_path: str, keys1: List[str], keys2: List[str], 
                       chunk_size: int = 5000, sample_size: int = 1000) -> Dict:
    """
    High-level function to compare large files efficiently
    """
    comparateur = ComparateurFichiersOptimise(file1_path, file2_path, keys1, keys2, chunk_size)
    try:
        return comparateur.comparer_optimise(sample_size)
    finally:
        comparateur.cleanup()
