#!/usr/bin/env python
"""
Script to create initial admin user for DataAlign
Run this once after setting up the authentication system
"""

from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash
import sys

def create_admin_user():
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(role='admin').first()
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.username}")
            return
        
        # Create admin user
        admin_user = User(
            username='testVikinn',
            email='admin@dataalign.com',
            full_name='Administrator',
            password_hash=generate_password_hash('admin123'),  # Change this password!
            role='admin',
            is_active=True
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created successfully!")
            print("Username: testVikinn")
            print("Password: admin123")
            print("⚠️  Please change the password after first login!")
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.session.rollback()

def create_test_user():
    app = create_app()
    
    with app.app_context():
        # Check if test user already exists
        existing_user = User.query.filter_by(username='testuser').first()
        if existing_user:
            print(f"Test user already exists: {existing_user.username}")
            return
        
        # Create test user
        test_user = User(
            username='testuser',
            email='test@dataalign.com',
            full_name='Test User',
            password_hash=generate_password_hash('test123'),
            role='user',
            is_active=True
        )
        
        try:
            db.session.add(test_user)
            db.session.commit()
            print("✅ Test user created successfully!")
            print("Username: testuser")
            print("Password: test123")
            
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            db.session.rollback()

if __name__ == '__main__':
    print("🔧 Creating initial users for DataAlign...")
    
    create_admin_user()
    create_test_user()
    
    print("\n🚀 Setup complete! You can now login to the application.")
    print("Admin access: admin / admin123")
    print("User access: testuser / test123")
    print("\n⚠️  Remember to change the default passwords!")
