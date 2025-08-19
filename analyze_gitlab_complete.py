#!/usr/bin/env python3
"""
Analyseur complet du fichier .gitlab-ci.yml
Détecte tous les problèmes potentiels
"""
import re
from pathlib import Path

def analyze_gitlab_ci():
    """Analyse complète du fichier .gitlab-ci.yml"""
    gitlab_file = Path('.gitlab-ci.yml')
    
    if not gitlab_file.exists():
        print("❌ Fichier .gitlab-ci.yml introuvable")
        return False
    
    try:
        with open(gitlab_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        print(f"📄 Analyse de {len(lines)} lignes")
        print("=" * 60)
        
        issues = []
        warnings = []
        
        # 1. Analyse syntaxe YAML
        print("🔍 ANALYSE SYNTAXE YAML")
        print("-" * 30)
        
        for i, line in enumerate(lines, 1):
            line_content = line.rstrip()
            
            # Tabulations
            if '\t' in line:
                issues.append(f"Ligne {i}: Tabulation détectée (utiliser espaces)")
            
            # Caractères non-ASCII problématiques
            if any(ord(c) > 127 for c in line_content):
                non_ascii = [c for c in line_content if ord(c) > 127]
                warnings.append(f"Ligne {i}: Caractères non-ASCII: {non_ascii}")
            
            # Guillemets non fermés
            if line_content.count('"') % 2 != 0:
                issues.append(f"Ligne {i}: Guillemets non fermés")
            
            # Indentation incorrecte
            if line_content.strip().startswith('-'):
                indent = len(line_content) - len(line_content.lstrip())
                if indent % 2 != 0:
                    issues.append(f"Ligne {i}: Indentation impaire")
        
        # 2. Structure GitLab CI
        print("🔍 ANALYSE STRUCTURE GITLAB CI")
        print("-" * 30)
        
        # Sections requises
        required_sections = ['stages:', 'build:', 'test:']
        for section in required_sections:
            if section not in content:
                issues.append(f"Section manquante: {section}")
            else:
                print(f"✅ {section}")
        
        # Variables
        if 'variables:' in content:
            print("✅ Section variables présente")
        else:
            warnings.append("Section variables manquante")
        
        # 3. Analyse des jobs
        print("\n🔍 ANALYSE DES JOBS")
        print("-" * 30)
        
        # Trouver tous les jobs
        job_pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*):(?:\s*&.*)?$'
        jobs = re.findall(job_pattern, content, re.MULTILINE)
        
        # Exclure les sections de configuration
        config_sections = ['stages', 'variables', 'cache', 'before_script']
        actual_jobs = [job for job in jobs if job not in config_sections]
        
        print(f"Jobs détectés: {actual_jobs}")
        
        for job in actual_jobs:
            job_section = extract_job_section(content, job)
            if job_section:
                analyze_job(job, job_section, issues, warnings)
        
        # 4. Analyse spécifique Docker
        print("\n🔍 ANALYSE DOCKER")
        print("-" * 30)
        
        if 'docker:' in content:
            print("✅ Configuration Docker détectée")
            
            # Vérifier version Docker
            if 'docker:24-cli' in content:
                print("✅ Version Docker moderne (24)")
            
            # Vérifier services DinD
            if 'docker:24-dind' in content:
                print("✅ Docker-in-Docker configuré")
            
            # Vérifier variables Docker
            if 'DOCKER_TLS_CERTDIR' in content:
                print("✅ TLS Docker configuré")
        
        # 5. Analyse des scripts
        print("\n🔍 ANALYSE DES SCRIPTS")
        print("-" * 30)
        
        # Scripts potentiellement problématiques
        problematic_patterns = [
            (r'cat\s*<<\s*EOF', "Blocs heredoc (incompatibles GitLab CI)"),
            (r'\|\s*\n\s*python\s*-', "Blocs Python multi-lignes"),
            (r'[^\\]&&', "Commandes chaînées sans échappement"),
            (r'sudo\s+', "Commandes sudo (non recommandées)"),
        ]
        
        for pattern, description in problematic_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                issues.append(f"Pattern problématique détecté: {description}")
        
        # 6. Analyse sécurité
        print("\n🔍 ANALYSE SÉCURITÉ")
        print("-" * 30)
        
        security_issues = []
        
        # Mots de passe en dur
        if re.search(r'password["\']?\s*[:=]\s*["\']?[^$\s]+', content, re.IGNORECASE):
            security_issues.append("Mots de passe potentiels en dur détectés")
        
        # Clés en dur
        if re.search(r'key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}', content, re.IGNORECASE):
            security_issues.append("Clés potentielles en dur détectées")
        
        # Variables sensibles non protégées
        sensitive_vars = ['SECRET_KEY', 'MAIL_PASSWORD', 'DATABASE_URL']
        for var in sensitive_vars:
            if f'{var}=' in content and not f'${{{var}}}' in content and not f'${{var}}' in content:
                security_issues.append(f"Variable sensible {var} potentiellement en dur")
        
        if security_issues:
            issues.extend(security_issues)
        else:
            print("✅ Pas de problème de sécurité évident")
        
        # 7. Analyse performance
        print("\n🔍 ANALYSE PERFORMANCE")
        print("-" * 30)
        
        if 'cache:' in content:
            print("✅ Cache configuré")
        else:
            warnings.append("Cache non configuré (performance)")
        
        if '--no-cache-dir' in content:
            print("✅ Cache pip désactivé (bonne pratique)")
        
        # 8. Résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DE L'ANALYSE")
        print("=" * 60)
        
        print(f"📄 Lignes analysées: {len(lines)}")
        print(f"🏗️ Jobs détectés: {len(actual_jobs)}")
        print(f"❌ Problèmes critiques: {len(issues)}")
        print(f"⚠️ Avertissements: {len(warnings)}")
        
        if issues:
            print(f"\n❌ PROBLÈMES CRITIQUES ({len(issues)}):")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        
        if warnings:
            print(f"\n⚠️ AVERTISSEMENTS ({len(warnings)}):")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")
        
        if not issues and not warnings:
            print("\n🎉 FICHIER PARFAIT!")
            print("✅ Aucun problème détecté")
            print("🚀 Prêt pour GitLab CI/CD")
            return True
        elif not issues:
            print("\n✅ FICHIER FONCTIONNEL")
            print("💡 Quelques améliorations possibles")
            return True
        else:
            print("\n❌ CORRECTIONS NÉCESSAIRES")
            print("🔧 Corrigez les problèmes critiques")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return False

def extract_job_section(content, job_name):
    """Extrait la section d'un job spécifique"""
    try:
        pattern = f'^{job_name}:.*?(?=^[a-zA-Z_]|\\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        return match.group(0) if match else None
    except:
        return None

def analyze_job(job_name, job_content, issues, warnings):
    """Analyse un job spécifique"""
    print(f"  📋 Analyse job: {job_name}")
    
    # Vérifier structure minimale
    required_job_keys = ['stage', 'script']
    for key in required_job_keys:
        if f'{key}:' not in job_content:
            issues.append(f"Job {job_name}: clé {key} manquante")
    
    # Vérifier only/except/rules
    if 'only:' not in job_content and 'except:' not in job_content and 'rules:' not in job_content:
        warnings.append(f"Job {job_name}: aucune condition d'exécution (only/except/rules)")
    
    # Vérifier image
    if 'image:' not in job_content:
        warnings.append(f"Job {job_name}: image Docker non spécifiée")
    
    # Vérifier scripts vides
    if 'script:' in job_content:
        script_match = re.search(r'script:\s*\n((?:\s*-.*\n)*)', job_content)
        if script_match and not script_match.group(1).strip():
            issues.append(f"Job {job_name}: script vide")
    
    print(f"    ✅ Job {job_name} analysé")

def main():
    print("🔍 ANALYSEUR COMPLET GITLAB-CI.YML")
    print("🎯 Détection de tous les problèmes potentiels")
    print("=" * 60)
    
    is_valid = analyze_gitlab_ci()
    
    print("\n" + "=" * 60)
    if is_valid:
        print("🎊 ANALYSE TERMINÉE - FICHIER PRÊT!")
    else:
        print("🔧 ANALYSE TERMINÉE - CORRECTIONS NÉCESSAIRES")

if __name__ == "__main__":
    main()
