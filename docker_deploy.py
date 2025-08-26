#!/usr/bin/env python3
"""
Docker deployment script for DataAlign v2.0
Provides easy commands to start, stop, and manage Docker containers
"""

import os
import sys
import subprocess
import argparse
import time
import secrets
import string

def run_command(command, shell=True, check=True):
    """Execute a command and return the result"""
    try:
        print(f"🔄 Executing: {command}")
        result = subprocess.run(command, shell=shell, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return None

def generate_secure_password(length=16):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secret_key(length=50):
    """Generate a secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def setup_environment():
    """Set up the environment files and directories"""
    print("🔧 Setting up DataAlign environment...")
    
    # Create necessary directories
    directories = ['uploads/source', 'uploads/archive', 'logs', 'temp', 'backups']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("📝 Creating .env file with secure passwords...")
        
        # Generate secure passwords
        secret_key = generate_secret_key()
        mysql_root_password = generate_secure_password(20)
        mysql_password = generate_secure_password(16)
        
        env_content = f"""# DataAlign Environment Configuration
# Generated automatically by docker_deploy.py

# Security
SECRET_KEY={secret_key}

# Database Configuration
MYSQL_ROOT_PASSWORD={mysql_root_password}
MYSQL_PASSWORD={mysql_password}

# Application Configuration
FLASK_ENV=production
DEBUG=False
AUTO_MIGRATION=false

# Database names
MYSQL_DATABASE=DataAlign_prod
MYSQL_USER=DataAlign
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ .env file created with secure passwords!")
        print("🔐 Passwords have been automatically generated and saved to .env")
        
        # Save passwords to a separate file for reference
        with open('IMPORTANT_PASSWORDS.txt', 'w') as f:
            f.write("IMPORTANT: DataAlign Passwords\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"MySQL Root Password: {mysql_root_password}\n")
            f.write(f"MySQL DataAlign Password: {mysql_password}\n")
            f.write(f"Secret Key: {secret_key}\n\n")
            f.write("Keep this file secure and delete it after noting the passwords!\n")
        
        print("📋 Passwords also saved to IMPORTANT_PASSWORDS.txt (delete after reading!)")
    else:
        print("✅ .env file already exists")
    
    return True

def start_development():
    """Start development environment"""
    print("🚀 Starting DataAlign development environment...")
    
    # Set up environment first
    setup_environment()
    
    # Stop any existing containers
    run_command("docker-compose -f docker-compose.dev.yml down", check=False)
    
    # Start the development stack
    result = run_command("docker-compose -f docker-compose.dev.yml up --build -d")
    
    if result:
        print("\n✅ Development environment started successfully!")
        print("📍 Access points:")
        print("   • DataAlign App: http://localhost:5006")
        print("   • Adminer (DB): http://localhost:8080")
        print("   • MailHog: http://localhost:8025")
        print("\n🔍 View logs with: docker-compose -f docker-compose.dev.yml logs -f")
        print("\n👤 Default test users:")
        print("   • Admin: testVikinn / admin123")
        print("   • User: testuser / test123")
    
    return result is not None

def start_production():
    """Start production environment"""
    print("🚀 Starting DataAlign production environment...")
    
    # Set up environment first
    setup_environment()
    
    # Stop any existing containers
    run_command("docker-compose down", check=False)
    
    # Start the production stack
    result = run_command("docker-compose up --build -d")
    
    if result:
        print("\n✅ Production environment started successfully!")
        print("📍 Access points:")
        print("   • DataAlign App: http://localhost:5004")
        print("   • Nginx Proxy: http://localhost:80")
        print("\n🔍 View logs with: docker-compose logs -f")
        print("\n🔐 Important: Check IMPORTANT_PASSWORDS.txt for database credentials")
        print("⚠️  Remember to delete IMPORTANT_PASSWORDS.txt after noting the passwords!")
    
    return result is not None

def stop_environment(env='dev'):
    """Stop the specified environment"""
    compose_file = "docker-compose.dev.yml" if env == 'dev' else "docker-compose.yml"
    print(f"🛑 Stopping {env} environment...")
    
    result = run_command(f"docker-compose -f {compose_file} down")
    
    if result:
        print(f"✅ {env.capitalize()} environment stopped successfully!")
    
    return result is not None

def show_logs(env='dev', service=None):
    """Show logs for the specified environment"""
    compose_file = "docker-compose.dev.yml" if env == 'dev' else "docker-compose.yml"
    service_arg = f" {service}" if service else ""
    
    command = f"docker-compose -f {compose_file} logs -f{service_arg}"
    print(f"📋 Showing logs for {env} environment...")
    
    try:
        subprocess.run(command, shell=True)
    except KeyboardInterrupt:
        print("\n🔍 Log viewing stopped.")

def show_status(env='dev'):
    """Show status of containers"""
    compose_file = "docker-compose.dev.yml" if env == 'dev' else "docker-compose.yml"
    print(f"📊 Status of {env} environment:")
    
    run_command(f"docker-compose -f {compose_file} ps")

def main():
    parser = argparse.ArgumentParser(description="DataAlign Docker Management Script")
    parser.add_argument('action', choices=['start', 'stop', 'logs', 'status', 'restart', 'setup'], 
                       help="Action to perform")
    parser.add_argument('--env', choices=['dev', 'prod'], default='dev',
                       help="Environment (dev or prod)")
    parser.add_argument('--service', 
                       help="Specific service for logs command")
    
    args = parser.parse_args()
    
    if args.action == 'setup':
        print("🔧 Setting up DataAlign environment...")
        setup_environment()
        print("\n✅ Setup complete! You can now start the application with:")
        print("   python docker_deploy.py start --env dev")
        print("   python docker_deploy.py start --env prod")
    
    elif args.action == 'start':
        if args.env == 'dev':
            start_development()
        else:
            start_production()
    
    elif args.action == 'stop':
        stop_environment(args.env)
    
    elif args.action == 'logs':
        show_logs(args.env, args.service)
    
    elif args.action == 'status':
        show_status(args.env)
    
    elif args.action == 'restart':
        print(f"🔄 Restarting {args.env} environment...")
        stop_environment(args.env)
        time.sleep(2)
        if args.env == 'dev':
            start_development()
        else:
            start_production()

if __name__ == "__main__":
    main()
