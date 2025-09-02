#!/usr/bin/env python3
"""
DataAlign v2.0 - Docker Startup with Account Creation
Enhanced Docker management with automatic MySQL account setup
"""

import os
import sys
import time
import subprocess
import mysql.connector
from pathlib import Path

class DockerAccountManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.docker_compose_files = {
            'development': 'docker-compose.dev.yml',
            'production': 'docker-compose.yml'
        }
        
    def check_docker(self):
        """Check if Docker is installed and running"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                 capture_output=True, text=True, check=True)
            print(f"✅ Docker found: {result.stdout.strip()}")
            
            result = subprocess.run(['docker-compose', '--version'], 
                                 capture_output=True, text=True, check=True)
            print(f"✅ Docker Compose found: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker or Docker Compose not found!")
            return False
    
    def start_mysql_container(self, environment='development'):
        """Start MySQL container and wait for it to be ready"""
        compose_file = self.docker_compose_files[environment]
        
        print(f"🐳 Starting MySQL container ({environment})...")
        
        try:
            # Start only MySQL service first
            subprocess.run([
                'docker-compose', '-f', compose_file, 
                'up', '-d', 'db'
            ], check=True, cwd=self.project_root)
            
            # Wait for MySQL to be ready
            print("⏳ Waiting for MySQL to be ready...")
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    if environment == 'development':
                        conn = mysql.connector.connect(
                            host='localhost',
                            port=3307,
                            user='root',
                            password='root_dev_secure',
                            connection_timeout=5
                        )
                    else:
                        conn = mysql.connector.connect(
                            host='localhost',
                            port=3306,
                            user='root',
                            password='root',
                            connection_timeout=5
                        )
                    conn.close()
                    print("✅ MySQL is ready!")
                    return True
                except mysql.connector.Error:
                    if attempt < max_attempts - 1:
                        print(f"   Attempt {attempt + 1}/{max_attempts}...")
                        time.sleep(2)
                    else:
                        print("❌ MySQL failed to start within timeout")
                        return False
                        
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start MySQL: {e}")
            return False
    
    def verify_accounts(self, environment='development'):
        """Verify that all MySQL accounts were created successfully"""
        try:
            if environment == 'development':
                conn = mysql.connector.connect(
                    host='localhost',
                    port=3307,
                    user='root',
                    password='root_dev_secure'
                )
            else:
                conn = mysql.connector.connect(
                    host='localhost',
                    port=3306,
                    user='root',
                    password='root'
                )
            
            cursor = conn.cursor()
            
            # Check created users
            cursor.execute("SELECT User, Host FROM mysql.user WHERE User LIKE 'dataalign%' OR User = 'admin_user'")
            users = cursor.fetchall()
            
            print("👥 Created MySQL accounts:")
            for user, host in users:
                print(f"   ✅ {user}@{host}")
            
            # Check databases
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall() if 'dataalign' in db[0]]
            
            print("🗄️ Created databases:")
            for db in databases:
                print(f"   ✅ {db}")
            
            # Check app configuration
            cursor.execute("SELECT COUNT(*) FROM dataalign.app_config")
            config_count = cursor.fetchone()[0]
            print(f"⚙️ Configuration entries: {config_count}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except mysql.connector.Error as e:
            print(f"❌ Account verification failed: {e}")
            return False
    
    def start_full_stack(self, environment='development'):
        """Start the complete Docker stack"""
        compose_file = self.docker_compose_files[environment]
        
        print(f"🚀 Starting full DataAlign stack ({environment})...")
        
        try:
            subprocess.run([
                'docker-compose', '-f', compose_file, 
                'up', '-d'
            ], check=True, cwd=self.project_root)
            
            print("✅ All services started successfully!")
            
            if environment == 'development':
                print("\n🌐 Service URLs:")
                print("   📱 Application: http://localhost:5006")
                print("   🗄️ Adminer: http://localhost:8081")
                print("   📧 MailHog: http://localhost:8026")
            else:
                print("\n🌐 Service URLs:")
                print("   📱 Application: http://localhost:5000")
                print("   🗄️ Adminer: http://localhost:8080")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start services: {e}")
            return False
    
    def show_connection_info(self, environment='development'):
        """Display connection information for the created accounts"""
        print("\n🔗 MySQL Connection Information:")
        
        if environment == 'development':
            port = 3307
            accounts = [
                ('dataalign_dev', 'dev_secure_123', 'dataalign_dev', 'Main development'),
                ('dataalign_test', 'test123', 'dataalign_test', 'Testing'),
                ('dataalign_readonly', 'readonly123', 'dataalign_dev', 'Read-only access'),
                ('admin_user', 'admin456', '*', 'Admin access'),
                ('root', 'root_dev_secure', '*', 'Root access')
            ]
        else:
            port = 3306
            accounts = [
                ('dataalign', 'dataalign', 'dataalign', 'Main application'),
                ('dataalign_readonly', 'readonly123', 'dataalign', 'Read-only access'),
                ('admin_user', 'admin456', '*', 'Admin access'),
                ('root', 'root', '*', 'Root access')
            ]
        
        print(f"Host: localhost:{port}")
        print("\nAccounts:")
        for user, password, database, description in accounts:
            print(f"   👤 {user} / {password} → {database} ({description})")

def main():
    print("🐳 DataAlign v2.0 - Docker Account Manager")
    print("=" * 50)
    
    manager = DockerAccountManager()
    
    # Check Docker installation
    if not manager.check_docker():
        print("\n❌ Please install Docker first:")
        print("   https://docs.docker.com/get-docker/")
        sys.exit(1)
    
    # Ask for environment
    print("\n🌍 Select environment:")
    print("1. Development (recommended)")
    print("2. Production")
    
    choice = input("Enter choice (1-2) [1]: ").strip() or "1"
    environment = 'development' if choice == '1' else 'production'
    
    print(f"\n🎯 Selected: {environment.upper()}")
    
    # Start MySQL and verify account creation
    if not manager.start_mysql_container(environment):
        sys.exit(1)
    
    # Wait a bit for initialization scripts to complete
    print("⏳ Waiting for account creation scripts...")
    time.sleep(5)
    
    # Verify accounts were created
    if not manager.verify_accounts(environment):
        print("⚠️ Account verification failed, but continuing...")
    
    # Start remaining services
    if not manager.start_full_stack(environment):
        sys.exit(1)
    
    # Show connection information
    manager.show_connection_info(environment)
    
    print("\n🎉 DataAlign is ready!")
    print("👥 Test accounts:")
    print("   Admin: testVikinn / admin123")
    print("   User: testuser / test123")

if __name__ == "__main__":
    main()
