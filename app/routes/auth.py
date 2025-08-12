from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models.user import User
from app import db
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.', 'error')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=remember)
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('projets.index'))
    
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not full_name or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('auth.signup'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('auth.signup'))
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('auth.signup'))
        
        # Create new user (always as simple user)
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role='user'  # Always create as simple user
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Handle profile updates
        try:
            current_user.full_name = request.form.get('full_name')
            current_user.email = request.form.get('email')
            current_user.username = request.form.get('username')
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
        
        return redirect(url_for('auth.profile'))
    
    # GET request - show profile page
    # Get user statistics for the profile page
    user_stats = {
        'projects_count': 0,  # Will be updated when we add proper relationships
        'comparisons_count': 0,  # Will be updated when we add proper relationships  
        'pending_deletions': 0  # Will be updated when we add proper relationships
    }
    
    # For now, return basic profile without stats since relationships aren't set up
    return render_template('auth/profile.html', user_stats=user_stats)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.email = request.form.get('email')
        
        # Change password if provided
        new_password = request.form.get('new_password')
        if new_password:
            current_password = request.form.get('current_password')
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('auth.edit_profile'))
            
            confirm_password = request.form.get('confirm_password')
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('auth.edit_profile'))
            
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html')

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Handle password change requests"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate current password
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('auth.profile'))
    
    # Validate new password length
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return redirect(url_for('auth.profile'))
    
    # Validate password confirmation
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('auth.profile'))
    
    # Update password
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error changing password. Please try again.', 'error')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Route pour demander une réinitialisation de mot de passe"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Veuillez saisir votre adresse email', 'error')
            return render_template('auth/forgot_password.html')
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Format d\'email invalide', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.is_active:
            # Generate reset token
            token = user.generate_reset_token()
            
            try:
                db.session.commit()
                
                # For now, just show the reset link (you can implement email later)
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                flash(f'Lien de réinitialisation généré: {reset_url}', 'info')
                    
            except Exception as e:
                db.session.rollback()
                flash('Erreur lors de la génération du token. Veuillez réessayer.', 'error')
        else:
            # For security, always show success message even if email doesn't exist
            flash('Si cette adresse email existe dans notre système, un lien de réinitialisation a été généré', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Route pour réinitialiser le mot de passe avec un token"""
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Token de réinitialisation invalide ou expiré', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Veuillez remplir tous les champs', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password
        user.set_password(password)
        user.clear_reset_token()
        
        try:
            db.session.commit()
            flash('Votre mot de passe a été réinitialisé avec succès', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Erreur lors de la mise à jour du mot de passe', 'error')
    
    return render_template('auth/reset_password.html', token=token, user=user)

@auth_bp.route('/admin/reset-tokens')
@login_required
def admin_reset_tokens():
    """Route pour que les admins voient tous les tokens de réinitialisation"""
    if not current_user.is_admin():
        flash('Accès non autorisé', 'error')
        return redirect(url_for('projets.dashboard'))
    
    from datetime import datetime
    
    # Récupérer tous les utilisateurs avec des tokens actifs
    active_tokens = User.query.filter(User.reset_token.isnot(None)).all()
    
    # Calculer les statistiques
    total_users = User.query.count()
    total_tokens = len(active_tokens)
    
    now = datetime.utcnow()
    expired_tokens = sum(1 for user in active_tokens 
                        if user.reset_token_expires and user.reset_token_expires < now)
    active_valid_tokens = total_tokens - expired_tokens
    
    stats = {
        'total_users': total_users,
        'active_tokens': active_valid_tokens,
        'expired_tokens': expired_tokens
    }
    
    return render_template('auth/admin_reset_tokens.html', 
                         active_tokens=active_tokens, 
                         stats=stats)

@auth_bp.route('/admin/revoke-token/<int:user_id>', methods=['POST'])
@login_required
def admin_revoke_reset_token(user_id):
    """Route pour que les admins révoquent un token spécifique"""
    if not current_user.is_admin():
        flash('Accès non autorisé', 'error')
        return redirect(url_for('projets.dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.clear_reset_token()
    
    try:
        db.session.commit()
        flash(f'Token de réinitialisation révoqué pour {user.username}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erreur lors de la révocation du token', 'error')
    
    return redirect(url_for('auth.admin_reset_tokens'))

@auth_bp.route('/admin/cleanup-expired-tokens', methods=['POST'])
@login_required
def admin_cleanup_expired_tokens():
    """Route pour nettoyer tous les tokens expirés"""
    if not current_user.is_admin():
        flash('Accès non autorisé', 'error')
        return redirect(url_for('projets.dashboard'))
    
    from datetime import datetime
    
    # Trouver tous les tokens expirés
    now = datetime.utcnow()
    expired_users = User.query.filter(
        User.reset_token.isnot(None),
        User.reset_token_expires < now
    ).all()
    
    count = 0
    for user in expired_users:
        user.clear_reset_token()
        count += 1
    
    try:
        db.session.commit()
        flash(f'{count} token(s) expiré(s) nettoyé(s)', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erreur lors du nettoyage des tokens', 'error')
    
    return redirect(url_for('auth.admin_reset_tokens'))

@auth_bp.route('/admin/revoke-all-tokens', methods=['POST'])
@login_required
def admin_revoke_all_tokens():
    """Route pour révoquer tous les tokens actifs (urgence)"""
    if not current_user.is_admin():
        flash('Accès non autorisé', 'error')
        return redirect(url_for('projets.dashboard'))
    
    # Trouver tous les utilisateurs avec des tokens
    users_with_tokens = User.query.filter(User.reset_token.isnot(None)).all()
    
    count = 0
    for user in users_with_tokens:
        user.clear_reset_token()
        count += 1
    
    try:
        db.session.commit()
        flash(f'⚠️ TOUS les tokens de réinitialisation ont été révoqués ({count} tokens)', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('Erreur lors de la révocation des tokens', 'error')
    
    return redirect(url_for('auth.admin_reset_tokens'))
