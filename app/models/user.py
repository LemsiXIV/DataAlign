from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db

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
    
    # Note: Relationships will be established after fixing database schema
    # projets = db.relationship('Projet', backref='owner', lazy=True, cascade='all, delete-orphan')
    # deletion_requests = db.relationship('DeletionRequest', foreign_keys='DeletionRequest.user_id', backref='requester', lazy=True)
    
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
    
    def __repr__(self):
        return f'<User {self.username}>'

class DeletionRequest(db.Model):
    __tablename__ = 'deletion_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    projet_id = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    admin_comments = db.Column(db.Text)
    
    # Relationships - temporarily disabled to fix schema issues
    # Note: Will be re-enabled after proper foreign key setup
    # reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_requests')
    
    def __repr__(self):
        return f'<DeletionRequest {self.id} - Project {self.projet_id}>'
