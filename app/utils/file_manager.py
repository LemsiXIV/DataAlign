import os
import shutil
from typing import List, Optional
from flask import current_app

def delete_project_files(projet, fichier_genere=None):
    """
    Delete all files associated with a project or specific treatment.
    
    Args:
        projet: The Projet object
        fichier_genere: Optional FichierGenere object for specific treatment deletion
    
    Returns:
        dict: Summary of deletion operations
    """
    deleted_files = []
    failed_deletions = []
    files_checked = []  # For debugging
    
    try:
        # If specific treatment deletion
        if fichier_genere:
            files_to_delete = _get_treatment_files(fichier_genere)
            files_checked.extend(files_to_delete)
            deleted, failed = _delete_files(files_to_delete)
            deleted_files.extend(deleted)
            failed_deletions.extend(failed)
        else:
            # Full project deletion
            # Delete all treatment files first
            for treatment in projet.fichiers:
                files_to_delete = _get_treatment_files(treatment)
                files_checked.extend(files_to_delete)
                deleted, failed = _delete_files(files_to_delete)
                deleted_files.extend(deleted)
                failed_deletions.extend(failed)
            
            # Delete project source files
            project_files = _get_project_files(projet)
            files_checked.extend(project_files)
            deleted, failed = _delete_files(project_files)
            deleted_files.extend(deleted)
            failed_deletions.extend(failed)
            
            # Delete project archive directory if it exists and is empty
            if projet.emplacement_archive:
                _cleanup_empty_directories(projet.emplacement_archive)
        
        return {
            'success': True,
            'deleted_files': deleted_files,
            'failed_deletions': failed_deletions,
            'files_checked': files_checked,  # For debugging
            'total_deleted': len(deleted_files),
            'total_failed': len(failed_deletions)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'deleted_files': deleted_files,
            'failed_deletions': failed_deletions,
            'files_checked': files_checked
        }

def _get_treatment_files(fichier_genere) -> List[str]:
    """Get all file paths associated with a treatment."""
    files = []
    
    # Get the project's folder as a base path
    projet = fichier_genere.projet if hasattr(fichier_genere, 'projet') else None
    base_folder = None
    if projet:
        base_folder = projet.emplacement_source or projet.emplacement_archive
    
    # Individual generated files
    if fichier_genere.nom_fichier_excel:
        if base_folder and not os.path.isabs(fichier_genere.nom_fichier_excel):
            # If it's not an absolute path, assume it's in the project folder
            file_path = os.path.join(base_folder, fichier_genere.nom_fichier_excel)
        else:
            file_path = fichier_genere.nom_fichier_excel
        files.append(file_path)
    
    if fichier_genere.nom_fichier_pdf:
        if base_folder and not os.path.isabs(fichier_genere.nom_fichier_pdf):
            file_path = os.path.join(base_folder, fichier_genere.nom_fichier_pdf)
        else:
            file_path = fichier_genere.nom_fichier_pdf
        files.append(file_path)
    
    if fichier_genere.nom_fichier_graphe:
        if base_folder and not os.path.isabs(fichier_genere.nom_fichier_graphe):
            file_path = os.path.join(base_folder, fichier_genere.nom_fichier_graphe)
        else:
            file_path = fichier_genere.nom_fichier_graphe
        files.append(file_path)
    
    # Archive path (could be a directory or zip file)
    if fichier_genere.chemin_archive:
        files.append(fichier_genere.chemin_archive)
    
    return files

def _get_project_files(projet) -> List[str]:
    """Get all file paths associated with a project (excluding treatments)."""
    files = []
    
    # Get the project's source/archive folder
    project_folder = projet.emplacement_source or projet.emplacement_archive
    
    # Original uploaded files
    if projet.fichier_1:
        if project_folder:
            # Files are stored in the project folder
            file_path = os.path.join(project_folder, projet.fichier_1)
        else:
            # Fallback to just the filename if no folder info
            file_path = projet.fichier_1
        files.append(file_path)
    
    if projet.fichier_2:
        if project_folder:
            # Files are stored in the project folder
            file_path = os.path.join(project_folder, projet.fichier_2)
        else:
            # Fallback to just the filename if no folder info
            file_path = projet.fichier_2
        files.append(file_path)
    
    # Add the entire project directory if it exists
    if project_folder:
        files.append(project_folder)
    
    return files

def _delete_files(file_paths: List[str]) -> tuple[List[str], List[str]]:
    """
    Delete a list of files and directories.
    
    Returns:
        tuple: (successfully_deleted, failed_deletions)
    """
    deleted = []
    failed = []
    
    for file_path in file_paths:
        if not file_path:
            continue
            
        try:
            # Convert relative paths to absolute paths
            if not os.path.isabs(file_path):
                # First try relative to current working directory
                abs_path = os.path.abspath(file_path)
                if not os.path.exists(abs_path):
                    # If not found, try relative to uploads folder
                    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                    abs_path = os.path.join(upload_folder, file_path)
                file_path = abs_path
            
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted.append(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    deleted.append(file_path)
            else:
                # File doesn't exist, might already be deleted - log for debugging
                pass
                
        except Exception as e:
            failed.append(f"{file_path}: {str(e)}")
    
    return deleted, failed

def _cleanup_empty_directories(base_path: str):
    """Remove empty directories up the path tree."""
    if not base_path or not os.path.exists(base_path):
        return
    
    try:
        # Convert to absolute path if needed
        if not os.path.isabs(base_path):
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            base_path = os.path.join(upload_folder, base_path)
        
        # Only clean up if it's a directory and is empty
        if os.path.isdir(base_path) and not os.listdir(base_path):
            os.rmdir(base_path)
            
            # Try to clean up parent directories if they're also empty
            parent_dir = os.path.dirname(base_path)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            
            # Don't delete the uploads folder itself
            if parent_dir != upload_folder and parent_dir:
                _cleanup_empty_directories(parent_dir)
                
    except Exception as e:
        # Ignore cleanup errors - not critical
        pass

def get_file_cleanup_summary(deletion_result: dict) -> str:
    """Generate a human-readable summary of file deletion operations."""
    if not deletion_result.get('success'):
        return f"File cleanup failed: {deletion_result.get('error', 'Unknown error')}"
    
    total_deleted = deletion_result.get('total_deleted', 0)
    total_failed = deletion_result.get('total_failed', 0)
    
    if total_deleted == 0 and total_failed == 0:
        return "No files to clean up."
    
    summary = f"Cleaned up {total_deleted} file(s)"
    
    if total_failed > 0:
        summary += f", {total_failed} file(s) could not be deleted"
    
    return summary + "."
