from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user import User, DeletionRequest
from app.models.projet import Projet
from app.models.fichier_genere import FichierGenere
from app.models.logs import LogExecution
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
            # Update request status first
            deletion_request.status = 'approved'
            deletion_request.reviewed_at = datetime.utcnow()
            deletion_request.reviewed_by = current_user.id
            deletion_request.admin_comments = request.form.get('admin_comments', '')
            deletion_request.fichier_genere_id = None  # Set to NULL before deleting
            
            # Delete the treatment
            db.session.delete(fichier_genere)
            db.session.commit()
            
            # Log the action
            log_admin_action(
                action="Treatment Deletion Approved",
                details=f"Approved deletion request for treatment '{treatment_name}' requested by user '{request_user}'"
            )
            
            flash(f'Treatment "{treatment_name}" has been deleted.', 'success')
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
                details=f"Approved deletion request for project '{project_name}' (ID: {project_id}) requested by user '{request_user}'"
            )
            
            flash(f'Project "{project_name}" has been deleted.', 'success')
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
    
    flash(flash_message, 'info')
    return redirect(url_for('admin.pending_requests'))

@admin_bp.route('/projects')
@login_required
@admin_required
def projects():
    page = request.args.get('page', 1, type=int)
    projects = Projet.query.paginate(
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
        # Update project logs to set projet_id to NULL (preserve logs)
        for log in projet.logs:
            log.projet_id = None
        
        # Delete the project (cascade will handle related records except logs)
        db.session.delete(projet)
        db.session.commit()
        
        # Log the action (this will be a system log since the project is gone)
        log_admin_action(
            action="Direct Treatment Deletion",
            details=f"Directly deleted treatment '{projet_name}' (ID: {log_project_id}) owned by user '{project_owner}'"
        )
        
        flash(f'Treatment "{projet_name}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting project: {str(e)}', 'error')
    
    return redirect(url_for('admin.projects'))
