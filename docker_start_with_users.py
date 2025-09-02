#!/usr/bin/env python3
"""
DataAlign v2.0 - Docker Startup with User Creation
Simple script to start Docker with automatic user creation
"""

import subprocess
import sys
import time

def main():
    print("🐳 DataAlign v2.0 - Docker Startup")
    print("=" * 40)
    
    try:
        # Build and start containers
        print("🏗️ Building and starting containers...")
        subprocess.run([
            'docker-compose', 'up', '--build', '-d'
        ], check=True)
        
        print("⏳ Waiting for services to start...")
        time.sleep(10)
        
        # Show running containers
        print("\n📋 Running containers:")
        subprocess.run(['docker-compose', 'ps'], check=True)
        
        print("\n🌐 Access your application:")
        print("   📱 DataAlign: http://localhost:5000")
        print("   🗄️ Adminer: http://localhost:8080")
        
        print("\n👥 Default user accounts:")
        print("   👑 Admin: testVikinn / admin123")
        print("   👤 User: testuser / test123")
        print("   👑 Demo Admin: demo_admin / demo123")
        print("   👤 Demo User: demo_user / demo123")
        
        print("\n✅ DataAlign is ready!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Docker: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Startup interrupted")
        sys.exit(0)

if __name__ == "__main__":
    main()
