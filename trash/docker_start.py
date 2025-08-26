#!/usr/bin/env python3
"""
Script de démarrage rapide Docker pour DataAlign
"""
import subprocess
import sys
import time
from pathlib import Path

def run_command(command, description, critical=True):
    """Exécute une commande avec gestion d'erreur"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} - OK")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ERREUR: {e}")
        if e.stderr:
            print(f"   Erreur: {e.stderr.strip()[:200]}...")
        if critical:
            print("⚠️ Erreur critique - Arrêt")
            sys.exit(1)
        return None

def check_docker():
    """Vérifier que Docker est installé et disponible"""
    print("1️⃣ VÉRIFICATION DOCKER")
    print("-" * 40)
    
    # Vérifier Docker
    docker_version = run_command("docker --version", "Version Docker")
    if not docker_version:
        print("❌ Docker n'est pas installé ou non disponible")
        print("📝 Installez Docker depuis: https://docs.docker.com/get-docker/")
        sys.exit(1)
    
    # Vérifier Docker Compose
    compose_version = run_command("docker-compose --version", "Version Docker Compose", critical=False)
    if not compose_version:
        print("⚠️ Docker Compose non trouvé, tentative avec 'docker compose'")
        compose_version = run_command("docker compose version", "Version Docker Compose v2", critical=False)
    
    print("✅ Docker est prêt\n")

def build_image():
    """Construire l'image Docker"""
    print("2️⃣ CONSTRUCTION IMAGE DOCKER DEV")
    print("-" * 40)
    
    # Try different build approaches for compatibility
    build_commands = [
        # First try: Use docker-compose to build (recommended for dev)
        ("docker-compose -f docker-compose.dev.yml build --no-cache", "Construction via docker-compose"),
        # Fallback: Direct docker build with legacy builder
        ("DOCKER_BUILDKIT=0 docker build -f Dockerfile.dev -t dataalign:latest .", "Construction directe Docker"),
        # Last resort: Build without BuildKit explicitly
        ("docker build --progress=plain -f Dockerfile.dev -t dataalign:latest .", "Construction sans BuildKit")
    ]
    
    build_success = False
    for command, description in build_commands:
        print(f"🔄 Tentative: {description}...")
        result = run_command(command, description, critical=False)
        if result is not None:
            build_success = True
            break
        else:
            print(f"⚠️ {description} a échoué, tentative suivante...")
    
    if not build_success:
        print("❌ Toutes les méthodes de construction ont échoué")
        print("💡 Solutions possibles:")
        print("   1. Vérifiez que package.json existe")
        print("   2. Essayez manuellement:")
        print("      export DOCKER_BUILDKIT=0")
        print("      docker-compose -f docker-compose.dev.yml build --no-cache")
        print("   3. Si Tailwind CSS pose problème:")
        print("      touch app/static/dist/output.css")
        print("      docker-compose -f docker-compose.dev.yml build --no-cache")
        
        # Try one more fallback: skip build and use up --build
        print("🔄 Tentative finale: démarrage avec build automatique...")
        result = run_command(
            "docker-compose -f docker-compose.dev.yml up -d --build", 
            "Démarrage avec build automatique",
            critical=False
        )
        if result is not None:
            print("✅ Build automatique réussi, on continue...")
            return  # Skip the rest of the build function
        
        sys.exit(1)
    
    # Vérifier l'image
    run_command(
        "docker images | grep dataalign", 
        "Vérification image créée",
        critical=False
    )
    
    print("✅ Image Docker construite\n")

def start_development():
    """Démarrer en mode développement avec docker-compose.dev.yml"""
    print("3️⃣ DÉMARRAGE MODE DÉVELOPPEMENT")
    print("-" * 40)
    
    if not Path("docker-compose.dev.yml").exists():
        print("❌ Fichier docker-compose.dev.yml non trouvé")
        return False
    
    # Set timeouts for WSL
    run_command("export COMPOSE_HTTP_TIMEOUT=300", "Configuration timeout", critical=False)
    run_command("export DOCKER_CLIENT_TIMEOUT=300", "Configuration timeout Docker", critical=False)
    
    # Arrêter les services existants
    run_command(
        "docker-compose -f docker-compose.dev.yml down -v", 
        "Arrêt services existants", 
        critical=False
    )
    
    # Nettoyer Docker
    run_command(
        "docker system prune -f", 
        "Nettoyage Docker", 
        critical=False
    )
    
    # Démarrer MySQL d'abord et attendre qu'il soit prêt
    print("🔄 Démarrage MySQL...")
    run_command(
        "docker-compose -f docker-compose.dev.yml up -d mysql", 
        "Démarrage MySQL"
    )
    
    # Attendre que MySQL soit prêt avec health check
    print("⏳ Attente de la disponibilité de MySQL...")
    mysql_ready = False
    max_attempts = 12  # 2 minutes max
    
    for attempt in range(max_attempts):
        result = run_command(
            "docker-compose -f docker-compose.dev.yml exec -T mysql mysqladmin ping -h localhost -u root -pdev_root_password",
            f"Test MySQL (tentative {attempt + 1}/{max_attempts})",
            critical=False
        )
        if result is not None:
            mysql_ready = True
            print("✅ MySQL est prêt")
            break
        print(f"⏳ MySQL pas encore prêt, attente 10s...")
        time.sleep(10)
    
    if not mysql_ready:
        print("⚠️ MySQL semble prendre du temps à démarrer, on continue quand même...")
    
    # Démarrer tous les services
    run_command(
        "docker-compose -f docker-compose.dev.yml up -d", 
        "Démarrage de tous les services"
    )
    
    # Attendre que les services soient prêts
    print("⏳ Attente démarrage complet des services (30s)...")
    time.sleep(30)
    
    # Vérifier les services
    run_command(
        "docker-compose -f docker-compose.dev.yml ps", 
        "État des services"
    )
    
    return True

def show_info():
    """Afficher les informations de connexion"""
    print("4️⃣ INFORMATIONS DE CONNEXION")
    print("-" * 40)
    
    print("🌐 URLS DISPONIBLES:")
    print("   • Application: http://localhost:5006")
    print("   • Base de données (Adminer): http://localhost:8081")
    print("   • Emails (MailHog): http://localhost:8026")
    
    print("\n👤 COMPTES DE TEST:")
    print("   • Admin: testVikinn / admin123")
    print("   • User: testuser / test123")
    
    print("\n🗄️ BASE DE DONNÉES (Adminer):")
    print("   • Serveur: mysql")
    print("   • Utilisateur: DataAlign")
    print("   • Mot de passe: DataAlign")
    print("   • Base: DataAlign_dev")
    
    print("\n📧 EMAILS:")
    print("   • Les emails sont capturés par MailHog")
    print("   • Interface web: http://localhost:8026")
    
    print("\n🔧 COMMANDES UTILES:")
    print("   • Voir logs: docker-compose -f docker-compose.dev.yml logs -f app")
    print("   • Arrêter: docker-compose -f docker-compose.dev.yml down")
    print("   • Redémarrer: docker-compose -f docker-compose.dev.yml restart app")
    print("   • Shell container: docker-compose -f docker-compose.dev.yml exec app bash")

def quick_test():
    """Test rapide de l'application"""
    print("\n5️⃣ TEST RAPIDE")
    print("-" * 40)
    
    try:
        import requests
        
        # Test page d'accueil (port mis à jour)
        response = requests.get("http://localhost:5006", timeout=10)
        if response.status_code == 200:
            print("✅ Application accessible sur http://localhost:5006")
        else:
            print(f"⚠️ Application répond avec code: {response.status_code}")
        
        # Test page de login
        response = requests.get("http://localhost:5006/auth/login", timeout=10)
        if response.status_code == 200:
            print("✅ Page de login accessible")
        else:
            print(f"⚠️ Page de login code: {response.status_code}")
            
    except ImportError:
        print("⚠️ Module 'requests' non installé - test manuel requis")
        print("   Testez manuellement: http://localhost:5006")
    except Exception as e:
        print(f"⚠️ Erreur test: {e}")
        print("   Vérifiez manuellement: http://localhost:5006")

def main():
    """Fonction principale"""
    print("🐳 DÉMARRAGE RAPIDE DOCKER DEV - DATAALIGN")
    print("=" * 50)
    print("🎯 Configuration et lancement automatique (Mode DEV)")
    print("=" * 50 + "\n")
    
    try:
        # Vérifications
        check_docker()
        
        # Construction
        build_image()
        
        # Démarrage
        success = start_development()
        
        if success:
            # Informations
            show_info()
            
            # Test rapide
            quick_test()
            
            print("\n🎉 DATAALIGN DOCKER DEV EST PRÊT !")
            print("=" * 50)
            print("🌐 Ouvrez votre navigateur sur: http://localhost:5006")
            print("🔐 Connectez-vous avec: testVikinn / admin123")
            print("📧 Emails capturés sur: http://localhost:8026")
            print("\n📋 Pour arrêter: docker-compose -f docker-compose.dev.yml down")
            
        else:
            print("❌ Erreur lors du démarrage des services")
            
    except KeyboardInterrupt:
        print("\n⚠️ Démarrage interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
