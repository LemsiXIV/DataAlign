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
    print("2️⃣ CONSTRUCTION IMAGE DOCKER")
    print("-" * 40)
    
    # Build de l'image
    run_command(
        "docker build -t dataalign:latest .", 
        "Construction image DataAlign"
    )
    
    # Vérifier l'image
    run_command(
        "docker images dataalign:latest", 
        "Vérification image créée"
    )
    
    print("✅ Image Docker construite\n")

def start_development():
    """Démarrer en mode développement avec docker-compose"""
    print("3️⃣ DÉMARRAGE MODE DÉVELOPPEMENT")
    print("-" * 40)
    
    if not Path("docker-compose.yml").exists():
        print("❌ Fichier docker-compose.yml non trouvé")
        return False
    
    # Arrêter les services existants
    run_command(
        "docker-compose down", 
        "Arrêt services existants", 
        critical=False
    )
    
    # Démarrer les services
    run_command(
        "docker-compose up -d", 
        "Démarrage services en mode détaché"
    )
    
    # Attendre que les services soient prêts
    print("⏳ Attente démarrage des services (30s)...")
    time.sleep(30)
    
    # Vérifier les services
    run_command(
        "docker-compose ps", 
        "État des services"
    )
    
    return True

def show_info():
    """Afficher les informations de connexion"""
    print("4️⃣ INFORMATIONS DE CONNEXION")
    print("-" * 40)
    
    print("🌐 URLS DISPONIBLES:")
    print("   • Application: http://localhost:5000")
    print("   • Base de données (Adminer): http://localhost:8080")
    print("   • Emails (MailHog): http://localhost:8025")
    print("   • Redis: localhost:6379")
    
    print("\n👤 COMPTES DE TEST:")
    print("   • Admin: testVikinn / admin123")
    print("   • User: testuser / test123")
    
    print("\n🗄️ BASE DE DONNÉES (Adminer):")
    print("   • Serveur: mysql")
    print("   • Utilisateur: dataalign")
    print("   • Mot de passe: dataalign123")
    print("   • Base: dataalign_dev")
    
    print("\n📧 EMAILS:")
    print("   • Les emails sont capturés par MailHog")
    print("   • Interface web: http://localhost:8025")
    
    print("\n🔧 COMMANDES UTILES:")
    print("   • Voir logs: docker-compose logs -f dataalign")
    print("   • Arrêter: docker-compose down")
    print("   • Redémarrer: docker-compose restart dataalign")
    print("   • Shell container: docker-compose exec dataalign bash")

def quick_test():
    """Test rapide de l'application"""
    print("\n5️⃣ TEST RAPIDE")
    print("-" * 40)
    
    try:
        import requests
        
        # Test page d'accueil
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("✅ Application accessible sur http://localhost:5000")
        else:
            print(f"⚠️ Application répond avec code: {response.status_code}")
        
        # Test page de login
        response = requests.get("http://localhost:5000/auth/login", timeout=5)
        if response.status_code == 200:
            print("✅ Page de login accessible")
        else:
            print(f"⚠️ Page de login code: {response.status_code}")
            
    except ImportError:
        print("⚠️ Module 'requests' non installé - test manuel requis")
        print("   Testez manuellement: http://localhost:5000")
    except Exception as e:
        print(f"⚠️ Erreur test: {e}")
        print("   Vérifiez manuellement: http://localhost:5000")

def main():
    """Fonction principale"""
    print("🐳 DÉMARRAGE RAPIDE DOCKER - DATAALIGN")
    print("=" * 50)
    print("🎯 Configuration et lancement automatique")
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
            
            print("\n🎉 DATAALIGN DOCKER EST PRÊT !")
            print("=" * 50)
            print("🌐 Ouvrez votre navigateur sur: http://localhost:5000")
            print("🔐 Connectez-vous avec: testVikinn / admin123")
            print("📧 Emails capturés sur: http://localhost:8025")
            print("\n📋 Pour arrêter: docker-compose down")
            
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
