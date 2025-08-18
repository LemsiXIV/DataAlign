#!/usr/bin/env python3
"""
Script de vérification post-consolidation documentation
Vérifie que tout fonctionne après la simplification des fichiers MD
"""
import os
import sys
from pathlib import Path

def check_files():
    """Vérifier que les fichiers essentiels existent"""
    print("📁 VÉRIFICATION FICHIERS ESSENTIELS")
    print("-" * 40)
    
    essential_files = [
        "README_KICKSTART.md",
        "README.md", 
        "docker_start.py",
        "deploy.py",
        "maintenance.py",
        "bypass_migrations.py",
        "test_password_reset.py",
        "requirements.txt",
        "run.py",
        "Dockerfile",
        "docker-compose.yml",
        ".gitlab-ci.yml"
    ]
    
    missing_files = []
    
    for file in essential_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MANQUANT")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️ {len(missing_files)} fichiers manquants")
        return False
    else:
        print(f"\n✅ Tous les {len(essential_files)} fichiers essentiels présents")
        return True

def check_documentation():
    """Vérifier la documentation consolidée"""
    print("\n📚 VÉRIFICATION DOCUMENTATION")
    print("-" * 40)
    
    # Vérifier README_KICKSTART.md
    kickstart_path = Path("README_KICKSTART.md")
    if kickstart_path.exists():
        content = kickstart_path.read_text(encoding='utf-8')
        
        # Vérifier sections importantes
        sections = [
            "DÉMARRAGE ULTRA-RAPIDE",
            "DOCKER",
            "CI/CD",
            "SCRIPTS DE MAINTENANCE", 
            "RÉSOLUTION PROBLÈMES",
            "SYSTÈME EMAIL",
            "SÉCURITÉ"
        ]
        
        missing_sections = []
        for section in sections:
            if section.lower() in content.lower():
                print(f"✅ Section '{section}' présente")
            else:
                print(f"❌ Section '{section}' manquante")
                missing_sections.append(section)
        
        # Statistiques du fichier
        lines = len(content.split('\n'))
        chars = len(content)
        print(f"\n📊 README_KICKSTART.md : {lines} lignes, {chars:,} caractères")
        
        return len(missing_sections) == 0
    else:
        print("❌ README_KICKSTART.md introuvable")
        return False

def check_md_files():
    """Vérifier qu'on n'a que les fichiers MD nécessaires"""
    print("\n📄 VÉRIFICATION FICHIERS MD")
    print("-" * 40)
    
    md_files = list(Path(".").glob("*.md"))
    
    print(f"Fichiers .md trouvés : {len(md_files)}")
    for md_file in md_files:
        print(f"  • {md_file.name}")
    
    # On ne devrait avoir que README.md et README_KICKSTART.md
    expected_md = {"README.md", "README_KICKSTART.md"}
    actual_md = {f.name for f in md_files}
    
    if actual_md == expected_md:
        print("✅ Seulement les fichiers MD nécessaires présents")
        return True
    else:
        extra = actual_md - expected_md
        missing = expected_md - actual_md
        
        if extra:
            print(f"⚠️ Fichiers MD supplémentaires : {extra}")
        if missing:
            print(f"❌ Fichiers MD manquants : {missing}")
        
        return len(missing) == 0

def check_scripts():
    """Vérifier que les scripts principaux sont exécutables"""
    print("\n🔧 VÉRIFICATION SCRIPTS")
    print("-" * 40)
    
    scripts = [
        "docker_start.py",
        "deploy.py", 
        "maintenance.py",
        "bypass_migrations.py",
        "test_password_reset.py"
    ]
    
    all_ok = True
    
    for script in scripts:
        if Path(script).exists():
            try:
                # Test d'import basique
                import subprocess
                result = subprocess.run([sys.executable, "-m", "py_compile", script], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {script} - Syntaxe OK")
                else:
                    print(f"❌ {script} - Erreur syntaxe")
                    all_ok = False
            except Exception as e:
                print(f"⚠️ {script} - Erreur test: {e}")
                all_ok = False
        else:
            print(f"❌ {script} - Fichier manquant")
            all_ok = False
    
    return all_ok

def check_docker():
    """Vérifier configuration Docker"""
    print("\n🐳 VÉRIFICATION DOCKER")
    print("-" * 40)
    
    docker_files = [
        "Dockerfile",
        "docker-compose.yml", 
        "docker-compose.prod.yml",
        ".dockerignore"
    ]
    
    all_present = True
    
    for file in docker_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MANQUANT")
            all_present = False
    
    return all_present

def show_usage_summary():
    """Afficher un résumé d'utilisation"""
    print("\n🎯 RÉSUMÉ D'UTILISATION")
    print("=" * 50)
    print("📖 DOCUMENTATION CONSOLIDÉE :")
    print("   • README.md - Aperçu rapide + lien vers guide complet")
    print("   • README_KICKSTART.md - Guide complet tout-en-un")
    print("")
    print("🚀 DÉMARRAGE RAPIDE :")
    print("   Option 1 : python docker_start.py")
    print("   Option 2 : python deploy.py")
    print("   Option 3 : python maintenance.py && python run.py")
    print("")
    print("🧪 TESTS :")
    print("   • python test_password_reset.py - Test système reset")
    print("   • python test_docker.py - Test Docker (si installé)")
    print("   • python maintenance.py - Test général")
    print("")
    print("📚 AIDE :")
    print("   • Tout est dans README_KICKSTART.md")
    print("   • Recherche : Ctrl+F dans README_KICKSTART.md")

def main():
    """Fonction principale de vérification"""
    print("🔍 VÉRIFICATION POST-CONSOLIDATION DATAALIGN")
    print("=" * 60)
    print("🎯 Validation après simplification documentation")
    print("=" * 60)
    
    checks = [
        ("Fichiers essentiels", check_files),
        ("Documentation", check_documentation), 
        ("Fichiers MD", check_md_files),
        ("Scripts", check_scripts),
        ("Docker", check_docker)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Erreur dans {check_name}: {e}")
            results.append((check_name, False))
    
    # Résumé
    print("\n📋 RÉSUMÉ DES VÉRIFICATIONS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{check_name:<20} : {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Score : {passed}/{total} vérifications passées")
    
    if passed == total:
        print("🎉 TOUTES LES VÉRIFICATIONS SONT PASSÉES !")
        print("✅ Votre documentation consolidée est prête")
        
        show_usage_summary()
        
        return True
    else:
        print("⚠️ Certaines vérifications ont échoué")
        print("🔧 Vérifiez les erreurs ci-dessus")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
