from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.models.user import User, DeletionRequest
from app.models.projet import Projet
from app.models.fichier_genere import FichierGenere
from app.models.logs import LogExecution
from app.routes.notifications import create_notification
from app.utils.file_manager import delete_project_files, get_file_cleanup_summary
from app import db
from datetime import datetime
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def log_admin_action(action, details, status='succès', project_id=None):
    """Log admin actions with user information"""
    try:
        message = f"[ADMIN ACTION] User: {current_user.username} ({current_user.full_name}) | Action: {action} | Details: {details}"
        log_entry = LogExecution(
            projet_id=project_id,
            statut=status,
            message=message,
            date_execution=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"❌ Error logging admin action: {e}")

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You need administrator privileges to access this page.', 'error')
            return redirect(url_for('projets.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    total_users = User.query.count()
    total_projects = Projet.query.count()
    pending_deletions = DeletionRequest.query.filter_by(status='pending').count()
    admin_users = User.query.filter_by(role='admin').count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    # Use joins to eagerly load related objects for pending requests
    pending_requests = DeletionRequest.query.join(User, DeletionRequest.user_id == User.id)\
                                           .join(Projet, DeletionRequest.projet_id == Projet.id)\
                                           .filter(DeletionRequest.status == 'pending')\
                                           .limit(5).all()
    
    # Create stats dictionary to match template expectations
    stats = {
        'total_users': total_users,
        'total_projects': total_projects,
        'pending_deletions': pending_deletions,
        'admin_users': admin_users
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         pending_requests=pending_requests)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/toggle-role', methods=['POST'])
@login_required
@admin_required
def toggle_user_role(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'error')
        return redirect(url_for('admin.users'))
    
    # Store old role for logging
    old_role = user.role
    
    # Toggle role
    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    
    # Log the action
    log_admin_action(
        action="User Role Change",
        details=f"Changed user '{user.username}' role from '{old_role}' to '{user.role}'"
    )
    
    flash(f'User {user.username} role changed to {user.role}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    # Store old status for logging
    old_status = 'active' if user.is_active else 'inactive'
    
    # Toggle active status
    user.is_active = not user.is_active
    db.session.commit()
    
    # Log the action
    new_status = 'active' if user.is_active else 'inactive'
    status = 'activated' if user.is_active else 'deactivated'
    
    log_admin_action(
        action="User Status Change",
        details=f"Changed user '{user.username}' status from '{old_status}' to '{new_status}'"
    )
    
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/deletion-requests')
@login_required
@admin_required
def pending_requests():
    page = request.args.get('page', 1, type=int)
    # Get all pending deletion requests (both project and treatment)
    deletion_requests = DeletionRequest.query.filter(DeletionRequest.status == 'pending')\
                                           .paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/pending_requests.html', pending_requests=deletion_requests.items)

@admin_bp.route('/deletion-requests/<int:request_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_deletion_request(request_id):
    deletion_request = DeletionRequest.query.get_or_404(request_id)
    
    if deletion_request.fichier_genere_id:
        # Treatment deletion request
        fichier_genere = deletion_request.fichier_genere
        treatment_name = fichier_genere.nom_traitement_projet or f"Treatment {fichier_genere.id}"
        request_user = deletion_request.user.username
        
        try:
            # Delete associated files first
            file_deletion_result = delete_project_files(fichier_genere.projet, fichier_genere)
            file_cleanup_summary = get_file_cleanup_summary(file_deletion_result)
            
            # Update request status first
            deletion_request.status = 'approved'
            deletion_request.reviewed_at = datetime.utcnow()
            deletion_request.reviewed_by = current_user.id
            deletion_request.admin_comments = request.form.get('admin_comments', '')
            deletion_request.fichier_genere_id = None  # Set to NULL before deleting
            
            # Delete the treatment from database
            db.session.delete(fichier_genere)
            db.session.commit()
            
            # Log the action with file cleanup info
            log_admin_action(
                action="Treatment Deletion Approved",
                details=f"Approved deletion request for treatment '{treatment_name}' requested by user '{request_user}'. {file_cleanup_summary}"
            )
            
            # Create notification for the user
            create_notification(
                user_id=deletion_request.user_id,
                title="Treatment Deletion Approved",
                message=f"Your request to delete treatment '{treatment_name}' has been approved and the treatment has been deleted. {file_cleanup_summary}",
                notification_type='success',
                related_request_id=deletion_request.id
            )
            
            flash(f'Treatment "{treatment_name}" has been deleted. {file_cleanup_summary}', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting treatment: {str(e)}', 'error')
    else:
        # Legacy project deletion request (keep existing logic)
        projet = deletion_request.projet
        project_name = projet.nom_projet
        project_id = projet.id
        request_user = deletion_request.user.username
        
        try:
            # Delete associated files first
            file_deletion_result = delete_project_files(projet)
            file_cleanup_summary = get_file_cleanup_summary(file_deletion_result)
            
            # Update request status first and set projet_id to NULL to avoid constraint violation
            deletion_request.status = 'approved'
            deletion_request.reviewed_at = datetime.utcnow()
            deletion_request.reviewed_by = current_user.id
            deletion_request.admin_comments = request.form.get('admin_comments', '')
            deletion_request.projet_id = None  # Set to NULL before deleting project
            
            # Update project logs to set projet_id to NULL (preserve logs)
            for log in projet.logs:
                log.projet_id = None
            
            # Delete the project (cascade will handle related records except logs)
            db.session.delete(projet)
            db.session.commit()
            
            # Log the action (this will be a system log since the project is gone)
            log_admin_action(
                action="Project Deletion Approved",
                details=f"Approved deletion request for project '{project_name}' (ID: {project_id}) requested by user '{request_user}'. {file_cleanup_summary}"
            )
            
            # Create notification for the user
            create_notification(
                user_id=deletion_request.user_id,
                title="Project Deletion Approved",
                message=f"Your request to delete project '{project_name}' has been approved and the project has been deleted. {file_cleanup_summary}",
                notification_type='success',
                related_request_id=deletion_request.id
            )
            
            flash(f'Project "{project_name}" has been deleted. {file_cleanup_summary}', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting project: {str(e)}', 'error')
    
    return redirect(url_for('admin.pending_requests'))

@admin_bp.route('/deletion-requests/<int:request_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_deletion_request(request_id):
    deletion_request = DeletionRequest.query.get_or_404(request_id)
    
    if deletion_request.fichier_genere_id:
        # Treatment deletion request
        treatment_name = deletion_request.fichier_genere.nom_traitement_projet or f"Treatment {deletion_request.fichier_genere.id}"
        request_user = deletion_request.user.username
        log_message = f"Rejected deletion request for treatment '{treatment_name}' requested by user '{request_user}'"
        flash_message = 'Treatment deletion request has been rejected.'
    else:
        # Legacy project deletion request
        project_name = deletion_request.projet.nom_projet if deletion_request.projet else 'Unknown'
        project_id = deletion_request.projet.id if deletion_request.projet else 'Unknown'
        request_user = deletion_request.user.username
        log_message = f"Rejected deletion request for project '{project_name}' (ID: {project_id}) requested by user '{request_user}'"
        flash_message = 'Project deletion request has been rejected.'
    
    # Update request status
    deletion_request.status = 'rejected'
    deletion_request.reviewed_at = datetime.utcnow()
    deletion_request.reviewed_by = current_user.id
    deletion_request.admin_comments = request.form.get('admin_comments', '')
    
    db.session.commit()
    
    # Log the action
    log_admin_action(
        action="Deletion Request Rejected",
        details=log_message,
        project_id=deletion_request.projet_id
    )
    
    # Create notification for the user
    admin_message = deletion_request.admin_comments.strip() if deletion_request.admin_comments else ''
    notification_message = f"Your deletion request has been rejected."
    if admin_message:
        notification_message += f" Reason: {admin_message}"
    else:
        notification_message += " No additional reason was provided."
    
    create_notification(
        user_id=deletion_request.user_id,
        title="Deletion Request Rejected",
        message=notification_message,
        notification_type='warning',
        related_request_id=deletion_request.id
    )
    
    flash(flash_message, 'info')
    return redirect(url_for('admin.pending_requests'))

@admin_bp.route('/projects')
@login_required
@admin_required
def projects():
    page = request.args.get('page', 1, type=int)
    projects = Projet.query.options(joinedload(Projet.owner)).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/projects.html', projects=projects)

@admin_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_project(project_id):
    projet = Projet.query.get_or_404(project_id)
    projet_name = projet.nom_projet
    project_owner = projet.owner.username if projet.owner else 'Unknown'
    
    # Store info for logging before deletion
    log_project_id = projet.id
    
    try:
        # Delete associated files first
        file_deletion_result = delete_project_files(projet)
        file_cleanup_summary = get_file_cleanup_summary(file_deletion_result)
        
        # Update project logs to set projet_id to NULL (preserve logs)
        for log in projet.logs:
            log.projet_id = None
        
        # Delete the project (cascade will handle related records except logs)
        db.session.delete(projet)
        db.session.commit()
        
        # Log the action (this will be a system log since the project is gone)
        log_admin_action(
            action="Direct Project Deletion",
            details=f"Directly deleted project '{projet_name}' (ID: {log_project_id}) owned by user '{project_owner}'. {file_cleanup_summary}"
        )
        
        flash(f'Project "{projet_name}" has been deleted. {file_cleanup_summary}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting project: {str(e)}', 'error')
    
    return redirect(url_for('admin.projects'))

@admin_bp.route('/debug/project/<int:project_id>/files')
@login_required
@admin_required
def debug_project_files(project_id):
    """Debug route to check what files would be deleted for a project"""
    projet = Projet.query.get_or_404(project_id)
    
    # Get file information without actually deleting
    from app.utils.file_manager import _get_project_files, _get_treatment_files
    
    debug_info = {
        'project_info': {
            'id': projet.id,
            'nom_projet': projet.nom_projet,
            'fichier_1': projet.fichier_1,
            'fichier_2': projet.fichier_2,
            'emplacement_source': projet.emplacement_source,
            'emplacement_archive': projet.emplacement_archive,
            'user_id': projet.user_id
        },
        'project_files': _get_project_files(projet),
        'treatments': []
    }
    
    for treatment in projet.fichiers:
        treatment_info = {
            'id': treatment.id,
            'nom_traitement_projet': treatment.nom_traitement_projet,
            'nom_fichier_excel': treatment.nom_fichier_excel,
            'nom_fichier_pdf': treatment.nom_fichier_pdf,
            'nom_fichier_graphe': treatment.nom_fichier_graphe,
            'chemin_archive': treatment.chemin_archive,
            'files': _get_treatment_files(treatment)
        }
        debug_info['treatments'].append(treatment_info)
    
    # Check if files actually exist
    import os
    all_files = debug_info['project_files'].copy()
    for treatment in debug_info['treatments']:
        all_files.extend(treatment['files'])
    
    file_existence = {}
    for file_path in all_files:
        if file_path:
            # Check both absolute and relative to uploads
            abs_path = os.path.abspath(file_path) if not os.path.isabs(file_path) else file_path
            uploads_path = os.path.join('uploads', file_path) if not os.path.isabs(file_path) else file_path
            
            file_existence[file_path] = {
                'absolute_path': abs_path,
                'uploads_path': uploads_path,
                'exists_absolute': os.path.exists(abs_path),
                'exists_uploads': os.path.exists(uploads_path),
                'actual_path': abs_path if os.path.exists(abs_path) else (uploads_path if os.path.exists(uploads_path) else None)
            }
    
    debug_info['file_existence'] = file_existence
    
    return jsonify(debug_info)
