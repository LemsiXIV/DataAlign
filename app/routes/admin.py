from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user import User, DeletionRequest
from app.models.projet import Projet
from app import db
from datetime import datetime
from functools import wraps

admin_bp = Blueprint('admin', __name__)

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
    pending_requests = DeletionRequest.query.filter_by(status='pending').limit(5).all()
    
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
    
    # Toggle role
    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    
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
    
    # Toggle active status
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/deletion-requests')
@login_required
@admin_required
def pending_requests():
    page = request.args.get('page', 1, type=int)
    requests = DeletionRequest.query.filter_by(status='pending').paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/pending_requests.html', requests=requests)

@admin_bp.route('/deletion-requests/<int:request_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_deletion_request(request_id):
    deletion_request = DeletionRequest.query.get_or_404(request_id)
    
    # Delete the project
    projet = deletion_request.projet
    db.session.delete(projet)
    
    # Update request status
    deletion_request.status = 'approved'
    deletion_request.reviewed_at = datetime.utcnow()
    deletion_request.reviewed_by = current_user.id
    deletion_request.admin_comments = request.form.get('admin_comments', '')
    
    db.session.commit()
    
    flash(f'Project "{projet.nom}" has been deleted.', 'success')
    return redirect(url_for('admin.pending_requests'))

@admin_bp.route('/deletion-requests/<int:request_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_deletion_request(request_id):
    deletion_request = DeletionRequest.query.get_or_404(request_id)
    
    # Update request status
    deletion_request.status = 'rejected'
    deletion_request.reviewed_at = datetime.utcnow()
    deletion_request.reviewed_by = current_user.id
    deletion_request.admin_comments = request.form.get('admin_comments', '')
    
    db.session.commit()
    
    flash('Deletion request has been rejected.', 'info')
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
    projet_name = projet.nom
    
    db.session.delete(projet)
    db.session.commit()
    
    flash(f'Project "{projet_name}" has been deleted.', 'success')
    return redirect(url_for('admin.projects'))
