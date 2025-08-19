#!/usr/bin/env python3
"""
Correction simple du fichier .gitlab-ci.yml sans dépendances
"""
import re
from pathlib import Path

def fix_gitlab_ci_simple():
    """Corrige le problème de coverage dans .gitlab-ci.yml"""
    gitlab_file = Path('.gitlab-ci.yml')
    
    if not gitlab_file.exists():
        print("❌ Fichier .gitlab-ci.yml introuvable")
        return False
    
    try:
        print("🔍 Lecture du fichier .gitlab-ci.yml...")
        with open(gitlab_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📝 Contenu lu avec succès")
        
        # Créer backup
        backup_file = gitlab_file.with_suffix('.yml.backup')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📦 Backup créé : {backup_file}")
        
        # Corrections spécifiques
        original_content = content
        
        # 1. Corriger la section artifacts problématique
        problem_pattern = r'artifacts:\s*\n\s*reports:\s*\n\s*coverage:\s*coverage\.xml'
        if re.search(problem_pattern, content, re.MULTILINE):
            print("🔧 Correction de la section artifacts/reports/coverage...")
            content = re.sub(
                problem_pattern,
                'artifacts:\n    paths:\n      - coverage.xml',
                content,
                flags=re.MULTILINE
            )
        
        # 2. Nettoyer autres problèmes potentiels
        fixes = [
            # Enlever lignes coverage invalides
            (r'\s*coverage:\s*coverage\.xml\s*\n', ''),
            # Assurer indentation correcte
            (r'(\s*)reports:\s*\n\s*coverage:', r'\1paths:'),
        ]
        
        for pattern, replacement in fixes:
            if re.search(pattern, content):
                print(f"🔧 Application fix : {pattern}")
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Vérifier si des changements ont été faits
        if content != original_content:
            # Écrire version corrigée
            with open(gitlab_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Corrections appliquées au fichier .gitlab-ci.yml")
            
            # Afficher les lignes modifiées
            print("\n📋 MODIFICATIONS APPLIQUÉES :")
            print("-" * 40)
            lines_old = original_content.split('\n')
            lines_new = content.split('\n')
            
            for i, (old, new) in enumerate(zip(lines_old, lines_new)):
                if old != new:
                    print(f"Ligne {i+1}:")
                    print(f"  AVANT: {old}")
                    print(f"  APRÈS: {new}")
            
        else:
            print("ℹ️ Aucune modification nécessaire")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False

def verify_fix():
    """Vérifie que le fix a fonctionné"""
    gitlab_file = Path('.gitlab-ci.yml')
    
    try:
        with open(gitlab_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier que les problèmes sont corrigés
        issues = []
        
        if 'coverage: coverage.xml' in content:
            issues.append("❌ 'coverage: coverage.xml' encore présent")
        
        if re.search(r'reports:\s*\n\s*coverage:', content):
            issues.append("❌ 'reports: coverage:' encore présent")
        
        if not issues:
            print("✅ Toutes les corrections ont été appliquées")
            print("✅ Le fichier devrait maintenant être valide pour GitLab")
            return True
        else:
            print("⚠️ Problèmes restants :")
            for issue in issues:
                print(f"  {issue}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {e}")
        return False

def main():
    print("🔧 CORRECTION GITLAB-CI.YML")
    print("=" * 50)
    print("Problème : 'coverage' n'est pas une clé valide dans artifacts:reports")
    print("=" * 50)
    
    success = fix_gitlab_ci_simple()
    
    if success:
        print("\n🔍 VÉRIFICATION")
        print("-" * 30)
        verify_fix()
        
        print("\n🚀 PROCHAINES ÉTAPES")
        print("-" * 30)
        print("1. git add .gitlab-ci.yml")
        print("2. git commit -m 'fix: Remove invalid coverage key from gitlab-ci artifacts'")
        print("3. git push")
        print("\n✅ Votre pipeline GitLab devrait maintenant fonctionner !")
    else:
        print("❌ Échec de la correction")

if __name__ == "__main__":
    main()
