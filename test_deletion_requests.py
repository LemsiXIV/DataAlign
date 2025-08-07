#!/usr/bin/env python3
"""
Test script to check deletion requests
"""

from app import create_app
from app.models.user import DeletionRequest, User
from app.models.projet import Projet

def main():
    app = create_app()
    
    with app.app_context():
        print("=== Testing Deletion Requests ===")
        
        # Check total deletion requests
        total_requests = DeletionRequest.query.count()
        print(f"Total deletion requests: {total_requests}")
        
        # Check pending requests
        pending_requests = DeletionRequest.query.filter_by(status='pending').count()
        print(f"Pending deletion requests: {pending_requests}")
        
        # List all pending requests with details
        if pending_requests > 0:
            print("\n=== Pending Requests Details ===")
            requests = DeletionRequest.query.filter_by(status='pending').all()
            for req in requests:
                print(f"Request ID: {req.id}")
                print(f"  User: {req.user.username if req.user else 'Unknown'}")
                print(f"  Project: {req.projet.nom_projet if req.projet else 'Unknown'}")
                print(f"  Status: {req.status}")
                print(f"  Created: {req.created_at}")
                print(f"  Reason: {req.reason}")
                print("---")
        else:
            print("No pending deletion requests found.")
            
        # Test relationships
        print("\n=== Testing Relationships ===")
        try:
            # Test if we can create and access relationships
            users = User.query.limit(1).all()
            if users:
                user = users[0]
                print(f"Test user: {user.username}")
                print(f"User's projects count: {len(user.projets)}")
                
            projects = Projet.query.limit(1).all()
            if projects:
                project = projects[0]
                print(f"Test project: {project.nom_projet}")
                print(f"Project owner: {project.owner.username if project.owner else 'No owner'}")
                
        except Exception as e:
            print(f"Error testing relationships: {e}")

if __name__ == "__main__":
    main()
