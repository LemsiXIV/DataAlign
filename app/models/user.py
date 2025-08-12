from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from app import db
import secrets
import string

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'admin' or 'user'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Password Reset fields
    reset_token = db.Column(db.String(100), nullable=True, unique=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    projets = db.relationship('Projet', back_populates='owner', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def can_delete_project(self, projet):
        """Check if user can delete a project"""
        # For now, only admin can delete until we add owner_id to Projet model
        return self.is_admin()
    
    def can_edit_project(self, projet):
        """Check if user can edit a project"""
        # For now, only admin can edit until we add owner_id to Projet model
        return self.is_admin()
    
    def generate_reset_token(self):
        """Generate a secure reset token"""
        # Generate a random token
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for i in range(32))
        
        # Set token and expiration (24 hours)
        self.reset_token = token
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=24)
        
        return token
    
    def verify_reset_token(self, token):
        """Verify if the reset token is valid and not expired"""
        if not self.reset_token or not self.reset_token_expires:
            return False
        
        # Check if token matches and hasn't expired
        if (self.reset_token == token and 
            datetime.utcnow() < self.reset_token_expires):
            return True
        
        return False
    
    def clear_reset_token(self):
        """Clear the reset token after use"""
        self.reset_token = None
        self.reset_token_expires = None
    
    def __repr__(self):
        return f'<User {self.username}>'

class DeletionRequest(db.Model):
    __tablename__ = 'deletion_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    projet_id = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=True)  # Keep for backward compatibility
    fichier_genere_id = db.Column(db.Integer, db.ForeignKey('fichiers_generes.id'), nullable=True)  # New field for treatments
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    admin_comments = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='deletion_requests')
    projet = db.relationship('Projet', foreign_keys=[projet_id], backref='deletion_requests')
    fichier_genere = db.relationship('FichierGenere', foreign_keys=[fichier_genere_id], backref='deletion_requests')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_requests')
    
    def __repr__(self):
        return f'<DeletionRequest {self.id} - Project {self.projet_id}>'
