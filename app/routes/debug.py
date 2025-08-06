from flask import Blueprint, session, jsonify

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/debug/session')
def debug_session():
    """Debug route to check session contents"""
    return jsonify({
        'session_keys': list(session.keys()),
        'projet_id': session.get('projet_id'),
        'is_large_files': session.get('is_large_files'),
        'file1_name': session.get('file1_name'),
        'file2_name': session.get('file2_name'),
        'has_df_path': 'df_path' in session,
        'has_df2_path': 'df2_path' in session,
        'has_file1_path': 'file1_path' in session,
        'has_file2_path': 'file2_path' in session
    })
