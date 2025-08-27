#!/usr/bin/env python3
"""
One-command DataAlign startup script
Just run: python start.py
"""

import subprocess
import sys
import os

def main():
    print("🚀 DataAlign One-Command Startup")
    print("=" * 40)
    
    # Check if Docker is running
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("✅ Docker is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not running or not installed")
        print("Please install Docker and start Docker Desktop")
        sys.exit(1)
    
    # Check if docker-compose is available
    try:
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
        print("✅ Docker Compose is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker Compose is not available")
        print("Please install Docker Compose")
        sys.exit(1)
    
    print("\n🔧 Starting DataAlign development environment...")
    print("This will automatically:")
    print("  • Create necessary directories")
    print("  • Generate secure passwords")
    print("  • Set up database")
    print("  • Start all services")
    
    # Ask user if they want to continue
    response = input("\nContinue? (y/N): ").lower().strip()
    if response not in ['y', 'yes']:
        print("Cancelled.")
        sys.exit(0)
    
    # Start Docker containers with docker-compose
    try:
        print("\n🐳 Building and starting Docker containers...")
        subprocess.run(["docker-compose", "up", "--build", "-d"], check=True)
        
        print("\n" + "=" * 50)
        print("🎉 DataAlign is now running!")
        print("=" * 50)
        print("\n📍 Access your application:")
        print("   🌐 DataAlign App: http://localhost:5000")
        print("   🗄️  Database Admin: http://localhost:8080")
        print("\n👤 Test with these users:")
        print("   👨‍💼 Admin: testVikinn / admin123")
        print("   👤 User: testuser / test123")
        print("\n🔧 Useful commands:")
        print("   📋 View logs: docker-compose logs -f")
        print("   🛑 Stop: docker-compose down")
        print("   🔄 Restart: docker-compose restart")
        
    except subprocess.CalledProcessError:
        print("❌ Failed to start DataAlign")
        print("Check the error messages above")
        print("Try running: docker-compose down && docker-compose up --build")
        sys.exit(1)

if __name__ == "__main__":
    main()
