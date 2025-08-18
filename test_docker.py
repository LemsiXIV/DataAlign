#!/usr/bin/env python3
"""
Script de test Docker pour DataAlign
Valide que l'application fonctionne correctement dans un container
"""
import requests
import time
import sys
import subprocess
import json
from pathlib import Path

def run_command(command, description):
    """Exécute une commande avec gestion d'erreur"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} - OK")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ERREUR: {e}")
        print(f"Sortie d'erreur: {e.stderr}")
        return None

def test_docker_build():
    """Test de construction de l'image Docker"""
    print("1️⃣ TEST BUILD DOCKER IMAGE")
    print("-" * 40)
    
    # Build de l'image
    result = run_command(
        "docker build -t dataalign:test .", 
        "Construction image Docker"
    )
    
    if result is None:
        return False
    
    # Vérifier que l'image existe
    result = run_command(
        "docker images dataalign:test", 
        "Vérification image créée"
    )
    
    return result is not None

def test_docker_run():
    """Test de démarrage du container"""
    print("\n2️⃣ TEST DÉMARRAGE CONTAINER")
    print("-" * 40)
    
    # Arrêter container existant si il y en a un
    run_command(
        "docker stop dataalign-test 2>/dev/null || true", 
        "Arrêt container existant"
    )
    run_command(
        "docker rm dataalign-test 2>/dev/null || true", 
        "Suppression container existant"
    )
    
    # Démarrer nouveau container
    result = run_command(
        "docker run -d --name dataalign-test -p 5001:5000 dataalign:test", 
        "Démarrage container de test"
    )
    
    if result is None:
        return False
    
    # Attendre que l'application démarre
    print("⏳ Attente démarrage application (30s)...")
    time.sleep(30)
    
    # Vérifier que le container tourne
    result = run_command(
        "docker ps | grep dataalign-test", 
        "Vérification container actif"
    )
    
    return result is not None

def test_application_health():
    """Test de santé de l'application"""
    print("\n3️⃣ TEST SANTÉ APPLICATION")
    print("-" * 40)
    
    base_url = "http://localhost:5001"
    
    try:
        # Test page d'accueil
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Page d'accueil accessible")
        else:
            print(f"❌ Page d'accueil erreur: {response.status_code}")
            return False
        
        # Test page de login
        response = requests.get(f"{base_url}/auth/login", timeout=10)
        if response.status_code == 200:
            print("✅ Page de login accessible")
        else:
            print(f"❌ Page de login erreur: {response.status_code}")
            return False
        
        # Test page forgot password
        response = requests.get(f"{base_url}/auth/forgot-password", timeout=10)
        if response.status_code == 200:
            print("✅ Page reset password accessible")
        else:
            print(f"❌ Page reset password erreur: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur connexion application: {e}")
        return False

def test_database_connection():
    """Test de connexion à la base de données"""
    print("\n4️⃣ TEST CONNECTION BASE DE DONNÉES")
    print("-" * 40)
    
    try:
        # Test import de l'app dans le container
        result = run_command(
            "docker exec dataalign-test python -c \"from app import create_app; app = create_app(); print('✅ App créée avec succès')\"",
            "Test création app dans container"
        )
        
        if result and "✅ App créée avec succès" in result:
            print("✅ Application peut être créée dans le container")
            return True
        else:
            print("❌ Erreur création application")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test base de données: {e}")
        return False

def test_docker_logs():
    """Vérification des logs du container"""
    print("\n5️⃣ VÉRIFICATION LOGS")
    print("-" * 40)
    
    result = run_command(
        "docker logs dataalign-test", 
        "Récupération logs container"
    )
    
    if result:
        print("📋 Dernières lignes des logs:")
        lines = result.split('\n')[-10:]  # 10 dernières lignes
        for line in lines:
            if line.strip():
                print(f"   {line}")
        return True
    
    return False

def cleanup():
    """Nettoyage après tests"""
    print("\n6️⃣ NETTOYAGE")
    print("-" * 40)
    
    # Arrêter et supprimer le container de test
    run_command(
        "docker stop dataalign-test", 
        "Arrêt container de test"
    )
    run_command(
        "docker rm dataalign-test", 
        "Suppression container de test"
    )
    
    # Optionnel: supprimer l'image de test
    # run_command(
    #     "docker rmi dataalign:test", 
    #     "Suppression image de test"
    # )

def test_docker_compose():
    """Test avec docker-compose"""
    print("\n7️⃣ TEST DOCKER-COMPOSE (OPTIONNEL)")
    print("-" * 40)
    
    if not Path("docker-compose.yml").exists():
        print("⚠️ Fichier docker-compose.yml non trouvé")
        return True
    
    # Test de validation du fichier compose
    result = run_command(
        "docker-compose config", 
        "Validation fichier docker-compose"
    )
    
    return result is not None

def main():
    """Fonction principale de test"""
    print("🐳 TESTS DOCKER - DATAALIGN")
    print("=" * 50)
    print("🎯 Tests de l'image Docker et du déploiement")
    print("=" * 50)
    
    tests = [
        ("Build Docker", test_docker_build),
        ("Démarrage Container", test_docker_run),
        ("Santé Application", test_application_health),
        ("Connection BDD", test_database_connection),
        ("Logs Container", test_docker_logs),
        ("Docker Compose", test_docker_compose),
    ]
    
    results = []
    
    try:
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                if not result:
                    print(f"⚠️ Test '{test_name}' échoué")
            except Exception as e:
                print(f"❌ Erreur dans test '{test_name}': {e}")
                results.append((test_name, False))
        
        # Nettoyage
        cleanup()
        
        # Résumé
        print("\n🎯 RÉSUMÉ DES TESTS")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
            print(f"{test_name:<25} : {status}")
            if result:
                passed += 1
        
        print("-" * 50)
        print(f"Tests réussis: {passed}/{total}")
        
        if passed == total:
            print("🎉 TOUS LES TESTS DOCKER SONT PASSÉS !")
            print("🚀 Votre application DataAlign est prête pour Docker !")
            return True
        else:
            print("⚠️ Certains tests ont échoué")
            print("🔧 Vérifiez les erreurs ci-dessus")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrompus par l'utilisateur")
        cleanup()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
