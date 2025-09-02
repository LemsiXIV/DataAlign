#!/usr/bin/env python3
"""
One-command DataAlign startup script with automatic Docker setup
Just run: python start.py
"""

import subprocess
import sys
import os
import json
import platform
import webbrowser
import urllib.request
import re

def get_system_info():
    """Get system information for Docker installation"""
    system = platform.system().lower()
    architecture = platform.machine().lower()
    
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "mac"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"

def check_internet_connection():
    """Check if internet connection is available"""
    try:
        urllib.request.urlopen('https://www.google.com', timeout=5)
        return True
    except:
        return False

def get_latest_docker_version():
    """Get latest Docker version from GitHub API"""
    try:
        url = "https://api.github.com/repos/docker/docker-ce/releases/latest"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data['tag_name'].replace('v', '')
    except:
        return None

def get_current_docker_version():
    """Get currently installed Docker version"""
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, check=True)
        # Extract version from output like "Docker version 20.10.8, build 3967b7d"
        version_match = re.search(r'version (\d+\.\d+\.\d+)', result.stdout)
        if version_match:
            return version_match.group(1)
        return None
    except:
        return None

def get_current_compose_version():
    """Get currently installed Docker Compose version"""
    try:
        # Try docker-compose command first
        result = subprocess.run(["docker-compose", "--version"], 
                              capture_output=True, text=True, check=True)
        version_match = re.search(r'version (\d+\.\d+\.\d+)', result.stdout)
        if version_match:
            return version_match.group(1)
    except:
        pass
    
    try:
        # Try docker compose plugin
        result = subprocess.run(["docker", "compose", "version"], 
                              capture_output=True, text=True, check=True)
        version_match = re.search(r'version (\d+\.\d+\.\d+)', result.stdout)
        if version_match:
            return version_match.group(1)
    except:
        pass
    
    return None

def install_docker():
    """Guide user through Docker installation"""
    system = get_system_info()
    
    print("\n🔧 Docker Installation Guide")
    print("=" * 40)
    
    if system == "windows":
        print("For Windows:")
        print("1. Docker Desktop will be downloaded")
        print("2. Run the installer as Administrator")
        print("3. Restart your computer when prompted")
        print("4. Start Docker Desktop after restart")
        
        docker_url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
        print(f"\n📥 Opening download page: {docker_url}")
        webbrowser.open(docker_url)
        
    elif system == "mac":
        print("For macOS:")
        print("1. Docker Desktop will be downloaded")
        print("2. Open the .dmg file and drag Docker to Applications")
        print("3. Start Docker Desktop from Applications")
        
        # Detect Apple Silicon vs Intel
        if "arm" in platform.machine().lower():
            docker_url = "https://desktop.docker.com/mac/main/arm64/Docker.dmg"
        else:
            docker_url = "https://desktop.docker.com/mac/main/amd64/Docker.dmg"
        
        print(f"\n📥 Opening download page: {docker_url}")
        webbrowser.open(docker_url)
        
    elif system == "linux":
        print("For Linux:")
        print("1. We'll install Docker using the official script")
        print("2. This requires sudo privileges")
        
        try:
            print("\n📥 Downloading Docker installation script...")
            subprocess.run(["curl", "-fsSL", "https://get.docker.com", "-o", "get-docker.sh"], check=True)
            subprocess.run(["sudo", "sh", "get-docker.sh"], check=True)
            
            # Add user to docker group
            import getpass
            username = getpass.getuser()
            subprocess.run(["sudo", "usermod", "-aG", "docker", username], check=True)
            
            # Start Docker service
            try:
                subprocess.run(["sudo", "systemctl", "start", "docker"], check=True)
                subprocess.run(["sudo", "systemctl", "enable", "docker"], check=True)
                print("✅ Docker installed and started successfully!")
            except subprocess.CalledProcessError:
                print("⚠️  Docker installed but service start failed. You may need to start it manually.")
            
            print("⚠️  Please log out and log back in for group changes to take effect")
            print("    Or run: newgrp docker")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install Docker automatically")
            print("Please visit: https://docs.docker.com/engine/install/")
            return False
    
    else:
        print("❌ Unsupported operating system")
        print("Please visit: https://docs.docker.com/get-docker/")
        return False
    
    if system in ["windows", "mac"]:
        input("\n⏳ Press Enter after Docker installation is complete...")
        return True
    
    return False

def upgrade_docker():
    """Guide user through Docker upgrade"""
    system = get_system_info()
    
    print("\n🔄 Docker Upgrade Guide")
    print("=" * 40)
    
    if system in ["windows", "mac"]:
        print("For Docker Desktop:")
        print("1. Open Docker Desktop")
        print("2. Check for updates in Settings > General")
        print("3. Or download the latest version from the website")
        
        webbrowser.open("https://docs.docker.com/desktop/")
        input("\n⏳ Press Enter after Docker upgrade is complete...")
        
    elif system == "linux":
        print("For Linux:")
        print("Running Docker upgrade...")
        
        # Detect package manager and upgrade accordingly
        try:
            # Try apt (Ubuntu/Debian)
            if subprocess.run(["which", "apt"], capture_output=True).returncode == 0:
                print("📦 Using apt package manager...")
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "upgrade", "docker-ce", "docker-ce-cli", "containerd.io", "-y"], check=True)
                print("✅ Docker upgraded successfully via apt!")
            
            # Try yum (RHEL/CentOS)
            elif subprocess.run(["which", "yum"], capture_output=True).returncode == 0:
                print("📦 Using yum package manager...")
                subprocess.run(["sudo", "yum", "update", "docker-ce", "docker-ce-cli", "containerd.io", "-y"], check=True)
                print("✅ Docker upgraded successfully via yum!")
            
            # Try dnf (Fedora)
            elif subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
                print("📦 Using dnf package manager...")
                subprocess.run(["sudo", "dnf", "upgrade", "docker-ce", "docker-ce-cli", "containerd.io", "-y"], check=True)
                print("✅ Docker upgraded successfully via dnf!")
            
            # Try pacman (Arch Linux)
            elif subprocess.run(["which", "pacman"], capture_output=True).returncode == 0:
                print("📦 Using pacman package manager...")
                subprocess.run(["sudo", "pacman", "-Syu", "docker", "--noconfirm"], check=True)
                print("✅ Docker upgraded successfully via pacman!")
            
            else:
                print("⚠️  Unknown package manager. Please upgrade Docker manually:")
                print("   https://docs.docker.com/engine/install/")
                
        except subprocess.CalledProcessError:
            print("❌ Failed to upgrade Docker automatically")
            print("Please check your package manager or visit: https://docs.docker.com/engine/install/")
    
    return True

def check_docker_installation():
    """Check Docker installation and version"""
    print("🔍 Checking Docker installation...")
    
    # Check if Docker is installed
    current_version = get_current_docker_version()
    
    if not current_version:
        print("❌ Docker is not installed")
        
        if not check_internet_connection():
            print("❌ No internet connection. Cannot download Docker.")
            return False
        
        response = input("\n📦 Would you like to install Docker? (y/N): ").lower().strip()
        if response in ['y', 'yes']:
            if install_docker():
                print("\n🔄 Please restart this script after Docker installation")
                return False
        else:
            print("❌ Docker is required to run DataAlign")
            return False
    
    print(f"✅ Docker is installed (version {current_version})")
    
    # Check for updates if internet is available
    if check_internet_connection():
        print("🔍 Checking for Docker updates...")
        latest_version = get_latest_docker_version()
        
        if latest_version and current_version:
            # Try to install packaging module if needed
            if install_packaging_module():
                try:
                    from packaging import version
                    if version.parse(current_version) < version.parse(latest_version):
                        print(f"⚠️  Docker update available: {current_version} → {latest_version}")
                        response = input("\n🔄 Would you like to upgrade Docker? (y/N): ").lower().strip()
                        if response in ['y', 'yes']:
                            upgrade_docker()
                            return False  # Restart needed after upgrade
                    else:
                        print(f"✅ Docker is up to date ({current_version})")
                except ImportError:
                    print("⚠️  Cannot compare versions (packaging module not available)")
            else:
                # Simple string comparison as fallback
                if current_version != latest_version:
                    print(f"⚠️  Docker version differs: {current_version} vs latest {latest_version}")
                    response = input("\n🔄 Would you like to upgrade Docker? (y/N): ").lower().strip()
                    if response in ['y', 'yes']:
                        upgrade_docker()
                        return False
    else:
        print("⚠️  Cannot check for updates (no internet connection)")
    
    return True

def check_docker_compose():
    """Check Docker Compose installation"""
    print("\n🔍 Checking Docker Compose...")
    
    compose_version = get_current_compose_version()
    
    if not compose_version:
        print("❌ Docker Compose is not available")
        
        # Try to install compose plugin
        try:
            print("🔧 Attempting to install Docker Compose plugin...")
            result = subprocess.run(["docker", "compose", "version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Docker Compose plugin is available")
                return True
        except:
            pass
        
        # Offer to install Docker Compose on Linux
        system = get_system_info()
        if system == "linux":
            response = input("\n📦 Would you like to install Docker Compose? (y/N): ").lower().strip()
            if response in ['y', 'yes']:
                return install_docker_compose_linux()
        
        print("❌ Docker Compose is required")
        print("Please install Docker Compose:")
        print("https://docs.docker.com/compose/install/")
        return False
    
    print(f"✅ Docker Compose is available (version {compose_version})")
    return True

def install_docker_compose_linux():
    """Install Docker Compose on Linux"""
    try:
        print("📥 Installing Docker Compose...")
        
        # Get latest version
        url = "https://api.github.com/repos/docker/compose/releases/latest"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name']
        
        # Download and install
        architecture = platform.machine()
        if architecture == "x86_64":
            arch = "x86_64"
        elif architecture in ["aarch64", "arm64"]:
            arch = "aarch64"
        else:
            arch = "x86_64"  # fallback
        
        compose_url = f"https://github.com/docker/compose/releases/download/{latest_version}/docker-compose-linux-{arch}"
        
        subprocess.run([
            "sudo", "curl", "-L", compose_url, 
            "-o", "/usr/local/bin/docker-compose"
        ], check=True)
        
        subprocess.run(["sudo", "chmod", "+x", "/usr/local/bin/docker-compose"], check=True)
        
        # Verify installation
        result = subprocess.run(["docker-compose", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker Compose installed successfully!")
            return True
        else:
            print("❌ Docker Compose installation verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Failed to install Docker Compose: {e}")
        print("Please install manually: https://docs.docker.com/compose/install/")
        return False

def check_docker_running():
    """Check if Docker daemon is running"""
    print("\n🔍 Checking if Docker is running...")
    
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        print("✅ Docker daemon is running")
        return True
    except subprocess.CalledProcessError:
        print("❌ Docker daemon is not running")
        print("Please start Docker Desktop or the Docker service")
        return False
    
def install_packaging_module():
    """Install packaging module if not available"""
    try:
        import packaging
        return True
    except ImportError:
        print("📦 Installing packaging module for version comparison...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "packaging"], 
                         check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            print("⚠️  Could not install packaging module. Version comparison disabled.")
            return False

def main():
    print("� DataAlign Advanced Startup Script")
    print("=" * 50)
    print("This script will:")
    print("  • Check Docker installation and version")
    print("  • Install/upgrade Docker if needed")
    print("  • Verify Docker Compose availability")
    print("  • Start DataAlign development environment")
    
    # Step 1: Check Docker installation and version
    if not check_docker_installation():
        print("\n❌ Docker setup incomplete. Please restart the script.")
        sys.exit(1)
    
    # Step 2: Check Docker Compose
    if not check_docker_compose():
        print("\n❌ Docker Compose is required but not available.")
        sys.exit(1)
    
    # Step 3: Check if Docker daemon is running
    if not check_docker_running():
        print("\n❌ Please start Docker and try again.")
        sys.exit(1)

    print("\n🔧 Starting DataAlign development environment...")
    print("This will automatically:")
    print("  • Create necessary directories")
    print("  • Set up database with persistent storage")
    print("  • Start all services")
    
    # Ask user if they want to continue
    response = input("\nContinue with DataAlign startup? (y/N): ").lower().strip()
    if response not in ['y', 'yes']:
        print("Cancelled.")
        sys.exit(0)
    
    # Start Docker containers with docker-compose
    try:
        print("\n🐳 Building and starting Docker containers...")
        
        # Try docker-compose command first, then docker compose plugin
        compose_cmd = ["docker-compose", "up", "--build", "-d"]
        try:
            subprocess.run(compose_cmd, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to docker compose plugin
            compose_cmd = ["docker", "compose", "up", "--build", "-d"]
            subprocess.run(compose_cmd, check=True)
        
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
        print("   🗑️  Reset database: docker-compose down -v")
        print("\n💾 Note: Database data persists across restarts!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start DataAlign: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Check if ports 5000, 3306, 8080 are available")
        print("   2. Try: docker-compose down && docker-compose up --build")
        print("   3. Check Docker logs: docker-compose logs")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Startup cancelled by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
