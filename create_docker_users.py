#!/usr/bin/env python3
"""
DataAlign v2.0 - Docker User Creation Script
Automatically creates application users when container starts
"""

import os
import sys

# Add app directory to Python path (works both locally and in Docker)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, '/app')  # For Docker

def create_docker_users():
    """Create default users for Docker deployment"""
    
    try:
        from app import create_app, db
        from app.models.user import User
        from werkzeug.security import generate_password_hash
        
        # Create Flask app
        app = create_app()
        
        with app.app_context():
            # Ensure database tables exist
            try:
                db.create_all()
                print("📋 Database tables checked/created")
            except Exception as db_error:
                print(f"⚠️ Database setup warning: {db_error}")
            
            users_created = []
            
            # Default users to create
            default_users = [
                {
                    'username': 'testVikinn',
                    'email': 'admin@dataalign.com',
                    'full_name': 'Test Admin Vikinn',
                    'password': 'admin123',
                    'role': 'admin',
                    'description': '👑 Admin user with full access'
                },
                {
                    'username': 'testuser',
                    'email': 'user@dataalign.com',
                    'full_name': 'Test User',
                    'password': 'test123',
                    'role': 'user',
                    'description': '👤 Regular user with project access'
                }
            ]
            
            # Create users if they don't exist
            for user_data in default_users:
                try:
                    existing_user = User.query.filter_by(username=user_data['username']).first()
                    
                    if not existing_user:
                        new_user = User(
                            username=user_data['username'],
                            email=user_data['email'],
                            full_name=user_data['full_name'],
                            password_hash=generate_password_hash(user_data['password']),
                            role=user_data['role'],
                            is_active=True
                        )
                        
                        db.session.add(new_user)
                        users_created.append(f"{user_data['description']} - {user_data['username']} / {user_data['password']}")
                        print(f"✅ Created: {user_data['username']} ({user_data['description']})")
                    else:
                        print(f"⏭️ User already exists: {user_data['username']}")
                        
                except Exception as user_error:
                    print(f"❌ Error creating user {user_data['username']}: {user_error}")
                    continue
            
            # Commit changes
            if users_created:
                try:
                    db.session.commit()
                    print(f"\n🎉 Successfully created {len(users_created)} users!")
                    print("\n👥 Login Credentials:")
                    for user_info in users_created:
                        print(f"   {user_info}")
                except Exception as commit_error:
                    print(f"❌ Error committing users: {commit_error}")
                    db.session.rollback()
            else:
                print("ℹ️ All users already exist, no action needed")
            
            # Show all users summary
            try:
                all_users = User.query.all()
                print(f"\n📊 Total users in database: {len(all_users)}")
                for user in all_users:
                    role = "👑 Admin" if user.role == 'admin' else "👤 User"
                    print(f"   {role} {user.username} ({user.email})")
            except Exception as query_error:
                print(f"⚠️ Could not query users: {query_error}")
                
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        import traceback
        traceback.print_exc()
        
        # Don't exit with error in Docker - let the app continue
        if os.getenv('FLASK_ENV') == 'production':
            print("⚠️ Continuing startup despite user creation error...")
            return
        else:
            sys.exit(1)

if __name__ == "__main__":
    print("🐳 DataAlign Docker - Creating Initial Users")
    print("=" * 50)
    create_docker_users()
    print("✅ User creation completed!")
