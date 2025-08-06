import pandas as pd
import os
import sqlite3
from sqlalchemy import create_engine, text
from typing import Dict, List, Tuple, Iterator, Optional
import tempfile
import json
from datetime import datetime
from .memory_manager import MemoryManager, ChunkProcessor
from app import db

class ComparateurFichiersAvecMySQL:
    """
    Optimized file comparator that integrates with MySQL database
    Uses MySQL for persistent data and SQLite for temporary large file operations
    """
    
    def __init__(self, file1_path: str, file2_path: str, keys1: List[str], keys2: List[str], 
                 chunk_size: int = 5000, use_mysql_for_comparison: bool = False, 
                 mysql_connection_string: Optional[str] = None):
        self.file1_path = file1_path
        self.file2_path = file2_path
        self.keys1 = keys1
        self.keys2 = keys2
        self.chunk_size = chunk_size
        self.use_mysql_for_comparison = use_mysql_for_comparison
        self.memory_manager = MemoryManager()
        self.chunk_processor = ChunkProcessor(chunk_size)
        
        # MySQL connection for persistent data (projects, logs, etc.)
        self.mysql_engine = db.engine if mysql_connection_string is None else create_engine(mysql_connection_string)
        
        # Determine optimal processing strategy
        self._determine_processing_strategy()
        
        # Setup temporary processing database
        if self.processing_strategy == 'sqlite_temp':
            self._setup_sqlite_temp()
        elif self.processing_strategy == 'mysql_temp':
            self._setup_mysql_temp()
    
    def _determine_processing_strategy(self):
        """Determine the best processing strategy based on file sizes and available resources"""
        try:
            from .lecteur_fichier_optimise import LecteurFichierOptimise
            lecteur = LecteurFichierOptimise()
            file1_info = lecteur.read_file_info(self.file1_path)
            file2_info = lecteur.read_file_info(self.file2_path)
            
            total_rows = file1_info['total_rows'] + file2_info['total_rows']
            max_columns = max(file1_info['total_columns'], file2_info['total_columns'])
            
            print(f"File analysis: {total_rows} total rows, {max_columns} max columns")
            
            # Strategy decision logic
            if total_rows > 100000 or max_columns > 200:
                # Very large files - use SQLite for temporary processing
                self.processing_strategy = 'sqlite_temp'
                print("Using SQLite temporary database for very large files")
            elif total_rows > 20000 and self.use_mysql_for_comparison:
                # Medium files - can use MySQL temp tables if preferred
                self.processing_strategy = 'mysql_temp'
                print("Using MySQL temporary tables for medium files")
            else:
                # Small files - use in-memory processing
                self.processing_strategy = 'memory'
                print("Using in-memory processing for small files")
            
            # Adjust chunk size based on strategy
            if self.processing_strategy != 'memory':
                available_memory = self.memory_manager.get_memory_usage()['available_mb']
                optimal_chunk = self.chunk_processor.adaptive_chunk_size(total_rows, available_memory)
                self.chunk_size = min(optimal_chunk, 10000)  # Cap at 10k for database operations
                print(f"Using chunk size: {self.chunk_size}")
                
        except Exception as e:
            print(f"Could not analyze files, defaulting to memory processing: {e}")
            self.processing_strategy = 'memory'
    
    def _setup_sqlite_temp(self):
        """Setup temporary SQLite database for large file processing"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.sqlite_path = self.temp_db.name
        self.temp_db.close()
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        
        cursor = self.sqlite_conn.cursor()
        
        # Create optimized tables for comparison
        cursor.execute('''
            CREATE TABLE temp_file1 (
                id INTEGER PRIMARY KEY,
                composite_key TEXT,
                row_data TEXT,
                UNIQUE(composite_key)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE temp_file2 (
                id INTEGER PRIMARY KEY,
                composite_key TEXT,
                row_data TEXT,
                UNIQUE(composite_key)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX idx_temp_file1_key ON temp_file1(composite_key)')
        cursor.execute('CREATE INDEX idx_temp_file2_key ON temp_file2(composite_key)')
        
        self.sqlite_conn.commit()
    
    def _setup_mysql_temp(self):
        """Setup temporary MySQL tables for medium file processing"""
        # Generate unique table names to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        self.temp_table1 = f"temp_comparison_file1_{timestamp}"
        self.temp_table2 = f"temp_comparison_file2_{timestamp}"
        
        with self.mysql_engine.connect() as conn:
            # Create temporary tables
            conn.execute(text(f'''
                CREATE TEMPORARY TABLE {self.temp_table1} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    composite_key VARCHAR(500),
                    row_data JSON,
                    UNIQUE KEY unique_key (composite_key)
                ) ENGINE=InnoDB
            '''))
            
            conn.execute(text(f'''
                CREATE TEMPORARY TABLE {self.temp_table2} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    composite_key VARCHAR(500),
                    row_data JSON,
                    UNIQUE KEY unique_key (composite_key)
                ) ENGINE=InnoDB
            '''))
            
            conn.commit()
    
    def _read_file_chunks(self, file_path: str) -> Iterator[pd.DataFrame]:
        """Read file in chunks"""
        ext = file_path.split('.')[-1].lower()
        
        if ext == 'csv':
            chunk_iter = pd.read_csv(file_path, chunksize=self.chunk_size)
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
    
    def _load_file_to_sqlite(self, file_path: str, table_name: str, key_columns: List[str]):
        """Load file data into SQLite database in chunks"""
        cursor = self.sqlite_conn.cursor()
        processed_rows = 0
        
        print(f"Loading {file_path} into SQLite table {table_name}...")
        
        for chunk_idx, chunk in enumerate(self._read_file_chunks(file_path)):
            if chunk_idx % 10 == 0:
                memory_info = self.memory_manager.get_memory_usage()
                print(f"Processed {processed_rows} rows, Memory: {memory_info['rss_mb']:.1f} MB")
            
            chunk = self.memory_manager.optimize_dataframe_memory(chunk)
            
            batch_data = []
            for _, row in chunk.iterrows():
                composite_key = self._create_composite_key(row, key_columns)
                row_data = row.to_json()
                batch_data.append((composite_key, row_data))
            
            cursor.executemany(
                f'INSERT OR IGNORE INTO {table_name} (composite_key, row_data) VALUES (?, ?)',
                batch_data
            )
            
            processed_rows += len(chunk)
            
            if chunk_idx % 20 == 0:
                self.sqlite_conn.commit()
        
        self.sqlite_conn.commit()
        print(f"Loaded {processed_rows} rows into {table_name}")
    
    def _load_file_to_mysql(self, file_path: str, table_name: str, key_columns: List[str]):
        """Load file data into MySQL temporary table in chunks"""
        processed_rows = 0
        
        print(f"Loading {file_path} into MySQL table {table_name}...")
        
        with self.mysql_engine.connect() as conn:
            for chunk_idx, chunk in enumerate(self._read_file_chunks(file_path)):
                if chunk_idx % 5 == 0:
                    memory_info = self.memory_manager.get_memory_usage()
                    print(f"Processed {processed_rows} rows, Memory: {memory_info['rss_mb']:.1f} MB")
                
                chunk = self.memory_manager.optimize_dataframe_memory(chunk)
                
                batch_data = []
                for _, row in chunk.iterrows():
                    composite_key = self._create_composite_key(row, key_columns)
                    row_data = json.dumps(row.to_dict(), default=str)
                    batch_data.append((composite_key, row_data))
                
                # Insert in smaller batches for MySQL
                batch_size = 1000
                for i in range(0, len(batch_data), batch_size):
                    mini_batch = batch_data[i:i + batch_size]
                    placeholders = ', '.join(['(%s, %s)'] * len(mini_batch))
                    flat_data = [item for sublist in mini_batch for item in sublist]
                    
                    conn.execute(text(f'''
                        INSERT IGNORE INTO {table_name} (composite_key, row_data) 
                        VALUES {placeholders}
                    '''), flat_data)
                
                processed_rows += len(chunk)
                
                if chunk_idx % 10 == 0:
                    conn.commit()
            
            conn.commit()
        
        print(f"Loaded {processed_rows} rows into {table_name}")
    
    def comparer_optimise_avec_mysql(self, sample_size: int = 1000, projet_id: Optional[int] = None) -> Dict:
        """
        Optimized comparison method that integrates with MySQL for persistent data
        """
        def _perform_comparison():
            if self.processing_strategy == 'sqlite_temp':
                return self._compare_with_sqlite(sample_size, projet_id)
            elif self.processing_strategy == 'mysql_temp':
                return self._compare_with_mysql_temp(sample_size, projet_id)
            else:
                return self._compare_in_memory(sample_size, projet_id)
        
        try:
            return self.chunk_processor.process_with_memory_monitoring(_perform_comparison)
        except Exception as e:
            # Log error to MySQL
            if projet_id:
                self._log_to_mysql(projet_id, 'échec', f"Erreur lors de la comparaison: {str(e)}")
            raise e
    
    def _compare_with_sqlite(self, sample_size: int, projet_id: Optional[int]) -> Dict:
        """Compare using SQLite temporary database"""
        # Load files into SQLite
        self._load_file_to_sqlite(self.file1_path, 'temp_file1', self.keys1)
        self._load_file_to_sqlite(self.file2_path, 'temp_file2', self.keys2)
        
        # Get statistics
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM temp_file1')
        total_file1 = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM temp_file2')
        total_file2 = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM temp_file1 f1
            INNER JOIN temp_file2 f2 ON f1.composite_key = f2.composite_key
        ''')
        n_common = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM temp_file1 f1
            LEFT JOIN temp_file2 f2 ON f1.composite_key = f2.composite_key
            WHERE f2.composite_key IS NULL
        ''')
        n1 = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM temp_file2 f2
            LEFT JOIN temp_file1 f1 ON f2.composite_key = f1.composite_key
            WHERE f1.composite_key IS NULL
        ''')
        n2 = cursor.fetchone()[0]
        
        # Get sample data
        sample_data = self._get_sqlite_sample_data(sample_size)
        
        total = n1 + n2 + n_common
        
        results = {
            'n1': n1,
            'n2': n2,
            'n_common': n_common,
            'total': total,
            'nb_df': total_file1,
            'nb_df2': total_file2,
            'total_ecarts': n1 + n2,
            'pct1': round(n1 / total * 100, 2) if total > 0 else 0,
            'pct2': round(n2 / total * 100, 2) if total > 0 else 0,
            'pct_both': round(n_common / total * 100, 2) if total > 0 else 0,
            **sample_data
        }
        
        # Save results to MySQL
        if projet_id:
            self._save_results_to_mysql(results, projet_id)
        
        return results
    
    def _get_sqlite_sample_data(self, limit: int) -> Dict:
        """Get sample data from SQLite tables"""
        cursor = self.sqlite_conn.cursor()
        
        # Sample from differences
        cursor.execute('''
            SELECT f1.row_data FROM temp_file1 f1
            LEFT JOIN temp_file2 f2 ON f1.composite_key = f2.composite_key
            WHERE f2.composite_key IS NULL
            LIMIT ?
        ''', (limit,))
        
        ecarts_file1_data = [json.loads(row[0]) for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT f2.row_data FROM temp_file2 f2
            LEFT JOIN temp_file1 f1 ON f2.composite_key = f1.composite_key
            WHERE f1.composite_key IS NULL
            LIMIT ?
        ''', (limit,))
        
        ecarts_file2_data = [json.loads(row[0]) for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT f1.row_data FROM temp_file1 f1
            INNER JOIN temp_file2 f2 ON f1.composite_key = f2.composite_key
            LIMIT ?
        ''', (limit,))
        
        communs_data = [json.loads(row[0]) for row in cursor.fetchall()]
        
        return {
            'ecarts_fichier1': pd.DataFrame(ecarts_file1_data),
            'ecarts_fichier2': pd.DataFrame(ecarts_file2_data),
            'communs': pd.DataFrame(communs_data)
        }
    
    def _compare_in_memory(self, sample_size: int, projet_id: Optional[int]) -> Dict:
        """Fallback in-memory comparison for smaller files"""
        ext1 = self.file1_path.split('.')[-1].lower()
        ext2 = self.file2_path.split('.')[-1].lower()
        
        if ext1 == 'csv':
            df1 = pd.read_csv(self.file1_path)
        elif ext1 in ['xls', 'xlsx']:
            df1 = pd.read_excel(self.file1_path)
        
        if ext2 == 'csv':
            df2 = pd.read_csv(self.file2_path)
        elif ext2 in ['xls', 'xlsx']:
            df2 = pd.read_excel(self.file2_path)
        
        # Optimize memory
        df1 = self.memory_manager.optimize_dataframe_memory(df1)
        df2 = self.memory_manager.optimize_dataframe_memory(df2)
        
        # Create composite keys
        df1['_compare_key'] = df1[self.keys1].astype(str).agg('|'.join, axis=1)
        df2['_compare_key'] = df2[self.keys2].astype(str).agg('|'.join, axis=1)
        
        # Merge and compare
        merged = pd.merge(df1, df2, on='_compare_key', how='outer', indicator=True)
        
        ecarts_fichier1 = merged[merged['_merge'] == 'left_only']
        ecarts_fichier2 = merged[merged['_merge'] == 'right_only']
        communs = merged[merged['_merge'] == 'both']
        
        # Limit sample size for display
        if len(ecarts_fichier1) > sample_size:
            ecarts_fichier1 = ecarts_fichier1.sample(sample_size)
        if len(ecarts_fichier2) > sample_size:
            ecarts_fichier2 = ecarts_fichier2.sample(sample_size)
        if len(communs) > sample_size:
            communs = communs.sample(sample_size)
        
        total = len(merged)
        n1 = len(merged[merged['_merge'] == 'left_only'])
        n2 = len(merged[merged['_merge'] == 'right_only'])
        n_common = len(merged[merged['_merge'] == 'both'])
        
        results = {
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
        
        # Save results to MySQL
        if projet_id:
            self._save_results_to_mysql(results, projet_id)
        
        return results
    
    def _save_results_to_mysql(self, results: Dict, projet_id: int):
        """Save comparison results to MySQL database"""
        try:
            from app.models import StatistiqueEcart, ConfigurationCleComposee
            
            # Save configuration
            config1 = ConfigurationCleComposee(
                projet_id=projet_id,
                fichier='fichier1',
                champs_concatenes=','.join(self.keys1)
            )
            config2 = ConfigurationCleComposee(
                projet_id=projet_id,
                fichier='fichier2',
                champs_concatenes=','.join(self.keys2)
            )
            db.session.add_all([config1, config2])
            
            # Save statistics
            stat = StatistiqueEcart(
                projet_id=projet_id,
                nb_ecarts_uniquement_fichier1=results['n1'],
                nb_ecarts_uniquement_fichier2=results['n2'],
                nb_ecarts_communs=results['n_common'],
                date_execution=datetime.now()
            )
            db.session.add(stat)
            
            db.session.commit()
            
            # Log success
            self._log_to_mysql(projet_id, 'succès', 
                             f"Comparaison terminée: {results['n_common']} communs, "
                             f"{results['n1']} écarts fichier1, {results['n2']} écarts fichier2")
            
        except Exception as e:
            db.session.rollback()
            self._log_to_mysql(projet_id, 'échec', f"Erreur sauvegarde résultats: {str(e)}")
            print(f"Erreur lors de la sauvegarde des résultats: {e}")
    
    def _log_to_mysql(self, projet_id: int, statut: str, message: str):
        """Log execution information to MySQL"""
        try:
            from app.models.logs import LogExecution
            
            log = LogExecution(
                projet_id=projet_id,
                statut=statut,
                message=message
            )
            db.session.add(log)
            db.session.commit()
            
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du log: {e}")
    
    def cleanup(self):
        """Clean up temporary resources"""
        if self.processing_strategy == 'sqlite_temp' and hasattr(self, 'sqlite_conn'):
            self.sqlite_conn.close()
            if os.path.exists(self.sqlite_path):
                os.remove(self.sqlite_path)
        
        # MySQL temporary tables are automatically cleaned up when connection closes
        
        # Force garbage collection
        self.memory_manager.force_garbage_collection()
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()


# Convenience function that integrates with existing MySQL setup
def comparer_fichiers_avec_mysql(file1_path: str, file2_path: str, keys1: List[str], keys2: List[str], 
                                projet_id: Optional[int] = None, chunk_size: int = 5000, 
                                sample_size: int = 1000, use_mysql_temp: bool = False) -> Dict:
    """
    High-level function to compare files with full MySQL integration
    
    Args:
        file1_path: Path to first file
        file2_path: Path to second file
        keys1: Comparison keys for first file
        keys2: Comparison keys for second file
        projet_id: Project ID for saving results to MySQL
        chunk_size: Size of chunks for processing
        sample_size: Size of sample data to return
        use_mysql_temp: Whether to use MySQL temporary tables (vs SQLite) for medium files
    """
    comparateur = ComparateurFichiersAvecMySQL(
        file1_path, file2_path, keys1, keys2, 
        chunk_size=chunk_size, 
        use_mysql_for_comparison=use_mysql_temp
    )
    
    try:
        return comparateur.comparer_optimise_avec_mysql(sample_size, projet_id)
    finally:
        comparateur.cleanup()
