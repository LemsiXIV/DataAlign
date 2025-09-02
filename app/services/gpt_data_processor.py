import openai
import pandas as pd
import json
import os
import chardet
from typing import Optional, Dict, Any, List
from app.services.lecteur_fichier_optimise import LecteurFichierOptimise
import tempfile

class GPTDataProcessor:
    """Service to use GPT-4 for data cleaning, formatting and standardization"""
    
    def __init__(self, api_key: str = None):
        """Initialize GPT data processor with API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Initialize OpenAI client with new v1.0+ syntax
        self.client = openai.OpenAI(api_key=self.api_key)
        self.lecteur = LecteurFichierOptimise(chunk_size=100)  # Smaller chunks for GPT processing
    
    def detect_encoding(self, file_path: str) -> str:
        """Detect file encoding"""
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'
    
    def analyze_and_fix_file_structure(self, file_path: str) -> Dict[str, Any]:
        """Use GPT-4 to analyze raw file content and detect/fix structural issues"""
        
        # Read raw file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read(2048)  # First 2KB
        except UnicodeDecodeError:
            # Try with different encodings
            encodings = ['latin-1', 'windows-1252', 'cp1252']
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        raw_content = f.read(2048)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return {"error": "Cannot read file with supported encodings"}
        
        prompt = f"""
        Analysez ce contenu de fichier et détectez automatiquement les problèmes de structure:
        
        CONTENU DU FICHIER:
        {raw_content}
        
        ANALYSEZ ET DÉTECTEZ:
        1. Le délimiteur utilisé (virgule, point-virgule, tabulation, etc.)
        2. L'encodage du fichier 
        3. Les problèmes de structure (colonnes mal séparées, caractères spéciaux)
        4. La présence d'en-têtes
        5. Les incohérences de format
        
        RETOURNEZ UNE SOLUTION EN JSON:
        {{
            "detected_delimiter": ";",
            "detected_encoding": "utf-8", 
            "has_header": true,
            "column_count": 16,
            "structure_issues": ["Délimiteur point-virgule non détecté", "Colonnes fusionnées"],
            "recommended_fixes": ["Utiliser délimiteur ';'", "Re-parser avec bon délimiteur"],
            "pandas_read_params": {{
                "delimiter": ";",
                "encoding": "utf-8",
                "engine": "python",
                "on_bad_lines": "skip"
            }}
        }}
        """
        
        try:
            # Try GPT-4 first, then fallback to GPT-3.5-turbo if not available
            models_to_try = ["gpt-4", "gpt-3.5-turbo"]
            response = None
            
            for model in models_to_try:
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "Vous êtes un expert en analyse de fichiers de données. Analysez la structure et proposez des solutions précises en JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1000,
                        temperature=0.1,
                    )
                    print(f"✅ Using model: {model}")
                    break
                except Exception as model_error:
                    print(f"⚠️ Model {model} failed: {model_error}")
                    continue
            
            if not response:
                raise Exception("No available models")
            
            content = response.choices[0].message.content
            # Extract JSON from response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"Erreur GPT lors de l'analyse de structure: {e}")
            
            # Smart fallback: detect delimiter from raw content
            delimiter = ","
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_lines = [f.readline() for _ in range(3)]
                
                # Count delimiters in first few lines
                semicolon_count = sum(line.count(';') for line in first_lines)
                comma_count = sum(line.count(',') for line in first_lines)
                tab_count = sum(line.count('\t') for line in first_lines)
                
                # Choose delimiter with highest count
                if semicolon_count > comma_count and semicolon_count > tab_count:
                    delimiter = ";"
                elif tab_count > comma_count and tab_count > semicolon_count:
                    delimiter = "\t"
                else:
                    delimiter = ","
                    
                print(f"🔍 Fallback delimiter detection: '{delimiter}' (semicolons: {semicolon_count}, commas: {comma_count}, tabs: {tab_count})")
                
            except Exception as detect_error:
                print(f"⚠️ Could not detect delimiter: {detect_error}")
                delimiter = ","
            
            return {
                "detected_delimiter": delimiter,
                "detected_encoding": "utf-8",
                "has_header": True,
                "structure_issues": ["Analyse GPT non disponible"],
                "recommended_fixes": ["Utiliser paramètres par défaut"],
                "pandas_read_params": {
                    "delimiter": delimiter,
                    "encoding": "utf-8",
                    "engine": "python"
                }
            }
    
    def fix_file_with_gpt_analysis(self, file_path: str) -> pd.DataFrame:
        """Use GPT-4 analysis to properly read and fix file structure"""
        
        # Get GPT analysis
        analysis = self.analyze_and_fix_file_structure(file_path)
        
        # Apply recommended parameters
        read_params = analysis.get('pandas_read_params', {})
        
        try:
            # Read file with GPT-recommended parameters
            df = pd.read_csv(file_path, **read_params)
            
            print(f"✅ GPT-4 a détecté et corrigé la structure:")
            print(f"   - Délimiteur: '{read_params.get('delimiter', ',')}'")
            print(f"   - Encodage: {read_params.get('encoding', 'utf-8')}")
            print(f"   - Colonnes détectées: {len(df.columns)}")
            print(f"   - Problèmes résolus: {', '.join(analysis.get('structure_issues', []))}")
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur lors de l'application des corrections GPT: {e}")
            # Fallback to default reading
            return pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', engine='python')
    
    def analyze_data_structure(self, sample_data: pd.DataFrame) -> Dict[str, Any]:
        """Use GPT-4 to analyze data structure and suggest improvements"""
        # Convert sample to string representation
        sample_str = sample_data.head(10).to_string()
        
        prompt = f"""
        Analysez cette structure de données et identifiez:
        1. Les colonnes qui semblent contenir des identifiants ou clés uniques
        2. Les colonnes avec des problèmes de formatage (espaces, caractères spéciaux, incohérences)
        3. Les colonnes qui pourraient servir de clés de comparaison
        4. Suggestions d'amélioration du format
        
        Données d'exemple:
        {sample_str}
        
        Répondez en format JSON avec cette structure:
        {{
            "potential_keys": ["colonne1", "colonne2"],
            "formatting_issues": {{"colonne": "description du problème"}},
            "suggested_keys": ["meilleure_colonne_cle"],
            "data_quality_score": 85,
            "recommendations": ["suggestion1", "suggestion2"]
        }}
        """
        
        try:
            # Try GPT-4 first, then fallback to GPT-3.5-turbo if not available
            models_to_try = ["gpt-4", "gpt-3.5-turbo"]
            response = None
            
            for model in models_to_try:
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "Vous êtes un expert en analyse de données. Répondez uniquement en JSON valide."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1000,
                        temperature=0.1,
                    )
                    break
                except Exception as model_error:
                    print(f"⚠️ Model {model} failed: {model_error}")
                    continue
            
            if not response:
                raise Exception("No available models")
            
            content = response.choices[0].message.content
            # Extract JSON from response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"Erreur lors de l'analyse GPT: {e}")
            return {
                "potential_keys": [],
                "formatting_issues": {},
                "suggested_keys": [],
                "data_quality_score": 50,
                "recommendations": ["Analyse automatique non disponible"]
            }
    
    def clean_data_chunk(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean a DataFrame using basic standardization without GPT API call to avoid formatting issues"""
        if df.empty:
            return df
        
        # Make a copy to avoid modifying original
        cleaned_df = df.copy()
        
        try:
            # Basic data cleaning without API calls to maintain DataFrame structure
            for column in cleaned_df.columns:
                if cleaned_df[column].dtype == 'object':  # String columns
                    # Clean text data
                    cleaned_df[column] = cleaned_df[column].astype(str)
                    cleaned_df[column] = cleaned_df[column].str.strip()  # Remove whitespace
                    
                    # Standardize common patterns
                    # Fix date formats
                    if any(keyword in column.lower() for keyword in ['date', 'time', 'created', 'updated']):
                        cleaned_df[column] = self._standardize_dates(cleaned_df[column])
                    
                    # Fix currency/numeric values
                    elif any(keyword in column.lower() for keyword in ['price', 'amount', 'cost', 'value', 'total']):
                        cleaned_df[column] = self._standardize_currency(cleaned_df[column])
                    
                    # Standardize names/text
                    elif any(keyword in column.lower() for keyword in ['name', 'title', 'description']):
                        cleaned_df[column] = self._standardize_text(cleaned_df[column])
            
            return cleaned_df
            
        except Exception as e:
            print(f"Erreur lors du nettoyage local: {e}")
            return df  # Return original if cleaning fails
    
    def _standardize_dates(self, series: pd.Series) -> pd.Series:
        """Standardize date formats"""
        try:
            # Try to parse and standardize dates
            return pd.to_datetime(series, errors='coerce').dt.strftime('%Y-%m-%d')
        except:
            return series
    
    def _standardize_currency(self, series: pd.Series) -> pd.Series:
        """Standardize currency values"""
        try:
            # Remove currency symbols and standardize
            cleaned = series.str.replace(r'[€$£¥,]', '', regex=True)
            numeric = pd.to_numeric(cleaned, errors='coerce')
            return numeric.fillna(series)  # Keep original if conversion fails
        except:
            return series
    
    def _standardize_text(self, series: pd.Series) -> pd.Series:
        """Standardize text format"""
        try:
            # Title case for names, clean whitespace
            return series.str.title().str.replace(r'\s+', ' ', regex=True)
        except:
            return series
    
    def suggest_comparison_columns(self, df1_sample: pd.DataFrame, df2_sample: pd.DataFrame) -> Dict[str, Any]:
        """Use GPT-4 to suggest best columns for comparison between two datasets"""
        
        df1_info = f"Colonnes fichier 1: {list(df1_sample.columns)}\nAperçu:\n{df1_sample.head(5).to_string()}"
        df2_info = f"Colonnes fichier 2: {list(df2_sample.columns)}\nAperçu:\n{df2_sample.head(5).to_string()}"
        
        prompt = f"""
        Analysez ces deux datasets et suggérez la meilleure stratégie de comparaison:
        
        DATASET 1:
        {df1_info}
        
        DATASET 2:
        {df2_info}
        
        Identifiez:
        1. Les colonnes communes ou similaires qui peuvent servir de clés de jointure
        2. Les colonnes qui nécessitent une normalisation avant comparaison
        3. La meilleure stratégie de comparaison
        
        Répondez en JSON:
        {{
            "matching_columns": {{"df1_col": "df2_col"}},
            "suggested_keys": ["colonne1", "colonne2"],
            "normalization_needed": {{"column": "reason"}},
            "comparison_strategy": "description",
            "confidence_score": 85
        }}
        """
        
        try:
            # Try GPT-4 first, then fallback to GPT-3.5-turbo if not available
            models_to_try = ["gpt-4", "gpt-3.5-turbo"]
            response = None
            
            for model in models_to_try:
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "Vous êtes un expert en comparaison de données. Répondez en JSON valide."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1000,
                        temperature=0.1,
                    )
                    break
                except Exception as model_error:
                    print(f"⚠️ Model {model} failed: {model_error}")
                    continue
            
            if not response:
                raise Exception("No available models")
            
            content = response.choices[0].message.content
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"Erreur lors de l'analyse de comparaison GPT: {e}")
            return {
                "matching_columns": {},
                "suggested_keys": [],
                "normalization_needed": {},
                "comparison_strategy": "Comparaison standard",
                "confidence_score": 50
            }
    
    def process_file_for_comparison(self, file_path: str, cleaning_rules: Dict = None) -> Dict[str, Any]:
        """Process a file with GPT-4 enhancement for better comparison"""
        
        # Get file info and sample
        file_info = self.lecteur.read_file_info(file_path)
        sample_df = self.lecteur.get_file_sample(file_path, 100)
        
        # Analyze structure with GPT
        analysis = self.analyze_data_structure(sample_df)
        
        # Default cleaning rules
        default_rules = {
            "trim_whitespace": True,
            "normalize_case": False,
            "fix_encoding": True,
            "standardize_dates": True
        }
        
        if cleaning_rules:
            default_rules.update(cleaning_rules)
        
        # Process file in chunks if large
        if file_info['total_rows'] > 1000:
            print(f"Traitement du fichier volumineux en chunks ({file_info['total_rows']} lignes)")
            processed_chunks = []
            
            for i, chunk in enumerate(self.lecteur.read_file_chunks(file_path)):
                if i < 5:  # Limit GPT processing to first 5 chunks for cost control
                    cleaned_chunk = self.clean_data_chunk(chunk, default_rules)
                    processed_chunks.append(cleaned_chunk)
                else:
                    processed_chunks.append(chunk)
            
            # Combine chunks
            processed_df = pd.concat(processed_chunks, ignore_index=True)
        else:
            # Process small file entirely with GPT
            processed_df = self.clean_data_chunk(sample_df, default_rules)
        
        return {
            'processed_data': processed_df,
            'original_info': file_info,
            'gpt_analysis': analysis,
            'cleaning_applied': default_rules,
            'file_path': file_path
        }
    
    def enhance_comparison_config(self, file1_path: str, file2_path: str) -> Dict[str, Any]:
        """Generate enhanced comparison configuration using GPT analysis"""
        
        # Process both files
        file1_result = self.process_file_for_comparison(file1_path)
        file2_result = self.process_file_for_comparison(file2_path)
        
        # Get comparison suggestions
        comparison_suggestion = self.suggest_comparison_columns(
            file1_result['processed_data'].head(10),
            file2_result['processed_data'].head(10)
        )
        
        return {
            'file1': file1_result,
            'file2': file2_result,
            'comparison_config': comparison_suggestion,
            'recommended_keys': comparison_suggestion.get('suggested_keys', []),
            'processing_notes': {
                'file1_quality': file1_result['gpt_analysis'].get('data_quality_score', 'N/A'),
                'file2_quality': file2_result['gpt_analysis'].get('data_quality_score', 'N/A'),
                'confidence': comparison_suggestion.get('confidence_score', 'N/A')
            }
        }

def create_gpt_enhanced_comparison(file1_path: str, file2_path: str, api_key: str = None) -> Dict[str, Any]:
    """Convenience function to create GPT-enhanced comparison configuration"""
    processor = GPTDataProcessor(api_key)
    return processor.enhance_comparison_config(file1_path, file2_path)
