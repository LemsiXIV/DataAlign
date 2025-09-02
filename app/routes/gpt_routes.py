from flask import Blueprint, request, jsonify, session, current_app
from flask_login import login_required, current_user
from app.services.gpt_data_processor import GPTDataProcessor
from app.services.lecteur_fichier_optimise import LecteurFichierOptimise
import os
import tempfile
import json

gpt_bp = Blueprint('gpt', __name__, url_prefix='/gpt')

@gpt_bp.route('/analyze-file-structure', methods=['POST'])
@login_required
def analyze_file_structure():
    """Analyze file structure and detect delimiter/encoding issues"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        # Save temporarily
        temp_path = f"temp/structure_analysis_{file.filename}"
        os.makedirs("temp", exist_ok=True)
        file.save(temp_path)
        
        try:
            processor = GPTDataProcessor()
            analysis = processor.analyze_and_fix_file_structure(temp_path)
            
            return jsonify({
                'success': True,
                'analysis': analysis,
                'message': 'Analyse de structure terminée'
            })
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'analyse: {str(e)}'}), 500

@gpt_bp.route('/fix-file-structure', methods=['POST'])
@login_required
def fix_file_structure():
    """Fix file structure using GPT-4 analysis and return corrected data"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        # Save temporarily
        temp_path = f"temp/fix_structure_{file.filename}"
        os.makedirs("temp", exist_ok=True)
        file.save(temp_path)
        
        try:
            processor = GPTDataProcessor()
            
            # Analyze and fix
            analysis = processor.analyze_and_fix_file_structure(temp_path)
            fixed_df = processor.fix_file_with_gpt_analysis(temp_path)
            
            return jsonify({
                'success': True,
                'analysis': analysis,
                'columns': fixed_df.columns.tolist(),
                'sample_data': fixed_df.head(10).to_dict(orient='records'),
                'total_rows': len(fixed_df),
                'total_columns': len(fixed_df.columns),
                'message': f'Structure corrigée: {len(fixed_df.columns)} colonnes détectées'
            })
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la correction: {str(e)}'}), 500

@gpt_bp.route('/analyze-file', methods=['POST'])
@login_required
def analyze_file():
    """Analyze a file using GPT-4 to suggest improvements and cleaning"""
    
    if not current_app.config.get('ENABLE_GPT_PROCESSING'):
        return jsonify({
            'error': True,
            'message': 'GPT processing is not enabled'
        }), 400
    
    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key:
        return jsonify({
            'error': True,
            'message': 'OpenAI API key not configured'
        }), 400
    
    if 'file' not in request.files:
        return jsonify({
            'error': True,
            'message': 'No file provided'
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'error': True,
            'message': 'No file selected'
        }), 400
    
    try:
        # Save file temporarily
        temp_path = f"temp/gpt_analysis_{current_user.id}_{file.filename}"
        os.makedirs("temp", exist_ok=True)
        file.save(temp_path)
        
        # Initialize GPT processor
        processor = GPTDataProcessor(api_key)
        
        # Get file analysis
        result = processor.process_file_for_comparison(temp_path)
        
        # Store analysis in session for later use
        session[f'gpt_analysis_{file.filename}'] = {
            'temp_path': temp_path,
            'analysis': result['gpt_analysis'],
            'cleaning_rules': result['cleaning_applied'],
            'file_info': result['original_info']
        }
        
        return jsonify({
            'success': True,
            'analysis': result['gpt_analysis'],
            'file_info': result['original_info'],
            'cleaned_sample': result['processed_data'].head(10).to_dict(orient='records'),
            'recommendations': result['gpt_analysis'].get('recommendations', [])
        })
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            'error': True,
            'message': f'Error analyzing file: {str(e)}'
        }), 500

@gpt_bp.route('/suggest-comparison', methods=['POST'])
@login_required
def suggest_comparison():
    """Get GPT-4 suggestions for comparing two files"""
    
    if not current_app.config.get('ENABLE_GPT_PROCESSING'):
        return jsonify({
            'error': True,
            'message': 'GPT processing is not enabled'
        }), 400
    
    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key:
        return jsonify({
            'error': True,
            'message': 'OpenAI API key not configured'
        }), 400
    
    data = request.get_json()
    file1_name = data.get('file1_name')
    file2_name = data.get('file2_name')
    
    if not file1_name or not file2_name:
        return jsonify({
            'error': True,
            'message': 'Both file names are required'
        }), 400
    
    try:
        # Get stored analyses from session
        file1_analysis = session.get(f'gpt_analysis_{file1_name}')
        file2_analysis = session.get(f'gpt_analysis_{file2_name}')
        
        if not file1_analysis or not file2_analysis:
            return jsonify({
                'error': True,
                'message': 'Files must be analyzed first'
            }), 400
        
        # Initialize GPT processor
        processor = GPTDataProcessor(api_key)
        
        # Get samples from both files
        lecteur = LecteurFichierOptimise()
        file1_sample = lecteur.get_file_sample(file1_analysis['temp_path'], 10)
        file2_sample = lecteur.get_file_sample(file2_analysis['temp_path'], 10)
        
        # Get comparison suggestions
        comparison_config = processor.suggest_comparison_columns(file1_sample, file2_sample)
        
        return jsonify({
            'success': True,
            'comparison_config': comparison_config,
            'file1_quality': file1_analysis['analysis'].get('data_quality_score', 'N/A'),
            'file2_quality': file2_analysis['analysis'].get('data_quality_score', 'N/A'),
            'recommended_strategy': comparison_config.get('comparison_strategy', 'Standard comparison')
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error generating comparison suggestions: {str(e)}'
        }), 500

@gpt_bp.route('/apply-cleaning', methods=['POST'])
@login_required
def apply_cleaning():
    """Apply GPT-4 data cleaning to a file"""
    
    if not current_app.config.get('ENABLE_GPT_PROCESSING'):
        return jsonify({
            'error': True,
            'message': 'GPT processing is not enabled'
        }), 400
    
    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key:
        return jsonify({
            'error': True,
            'message': 'OpenAI API key not configured'
        }), 400
    
    data = request.get_json()
    file_name = data.get('file_name')
    cleaning_rules = data.get('cleaning_rules', {})
    
    if not file_name:
        return jsonify({
            'error': True,
            'message': 'File name is required'
        }), 400
    
    try:
        # Get stored analysis from session
        file_analysis = session.get(f'gpt_analysis_{file_name}')
        
        if not file_analysis:
            return jsonify({
                'error': True,
                'message': 'File must be analyzed first'
            }), 400
        
        # Initialize GPT processor
        processor = GPTDataProcessor(api_key)
        
        # Apply cleaning with custom rules
        result = processor.process_file_for_comparison(
            file_analysis['temp_path'], 
            cleaning_rules
        )
        
        # Save cleaned file to a new temp location
        cleaned_path = file_analysis['temp_path'].replace('.', '_cleaned.')
        result['processed_data'].to_csv(cleaned_path, index=False)
        
        # Update session with cleaned file path
        session[f'gpt_cleaned_{file_name}'] = cleaned_path
        
        return jsonify({
            'success': True,
            'message': 'Data cleaning applied successfully',
            'cleaned_sample': result['processed_data'].head(10).to_dict(orient='records'),
            'total_rows': len(result['processed_data']),
            'cleaning_applied': result['cleaning_applied']
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error applying data cleaning: {str(e)}'
        }), 500

@gpt_bp.route('/get-enhanced-config', methods=['POST'])
@login_required
def get_enhanced_config():
    """Get complete enhanced configuration for file comparison"""
    
    if not current_app.config.get('ENABLE_GPT_PROCESSING'):
        return jsonify({
            'error': True,
            'message': 'GPT processing is not enabled'
        }), 400
    
    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key:
        return jsonify({
            'error': True,
            'message': 'OpenAI API key not configured'
        }), 400
    
    data = request.get_json()
    file1_name = data.get('file1_name')
    file2_name = data.get('file2_name')
    
    if not file1_name or not file2_name:
        return jsonify({
            'error': True,
            'message': 'Both file names are required'
        }), 400
    
    try:
        # Check for cleaned versions first, then original
        file1_path = (session.get(f'gpt_cleaned_{file1_name}') or 
                     session.get(f'gpt_analysis_{file1_name}', {}).get('temp_path'))
        file2_path = (session.get(f'gpt_cleaned_{file2_name}') or 
                     session.get(f'gpt_analysis_{file2_name}', {}).get('temp_path'))
        
        if not file1_path or not file2_path:
            return jsonify({
                'error': True,
                'message': 'Files must be processed first'
            }), 400
        
        # Initialize GPT processor
        processor = GPTDataProcessor(api_key)
        
        # Get complete enhanced configuration
        config = processor.enhance_comparison_config(file1_path, file2_path)
        
        return jsonify({
            'success': True,
            'enhanced_config': config,
            'ready_for_comparison': True,
            'file_paths': {
                'file1': file1_path,
                'file2': file2_path
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error generating enhanced configuration: {str(e)}'
        }), 500

@gpt_bp.route('/cleanup-temp', methods=['POST'])
@login_required
def cleanup_temp():
    """Clean up temporary files created during GPT processing"""
    
    try:
        cleaned_count = 0
        
        # Clean up temp files from session
        keys_to_remove = []
        for key in session.keys():
            if key.startswith('gpt_analysis_') or key.startswith('gpt_cleaned_'):
                if key.startswith('gpt_analysis_'):
                    analysis = session[key]
                    temp_path = analysis.get('temp_path')
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)
                        cleaned_count += 1
                elif key.startswith('gpt_cleaned_'):
                    cleaned_path = session[key]
                    if os.path.exists(cleaned_path):
                        os.remove(cleaned_path)
                        cleaned_count += 1
                
                keys_to_remove.append(key)
        
        # Remove from session
        for key in keys_to_remove:
            session.pop(key, None)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {cleaned_count} temporary files'
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error during cleanup: {str(e)}'
        }), 500
