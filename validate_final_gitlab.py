#!/usr/bin/env python3
"""
Validation finale .gitlab-ci.yml
"""
import re
from pathlib import Path

def validate_gitlab_ci_syntax():
    """Valide la syntaxe du fichier .gitlab-ci.yml"""
    gitlab_file = Path('.gitlab-ci.yml')
    
    if not gitlab_file.exists():
        print("❌ Fichier .gitlab-ci.yml introuvable")
        return False
    
    try:
        with open(gitlab_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ Fichier lu avec succès")
        
        # Vérifications spécifiques
        issues = []
        
        # 1. Vérifier les blocs script problématiques
        if re.search(r'cat\s*<<\s*EOF', content):
            issues.append("❌ Blocs 'cat << EOF' détectés (incompatibles GitLab CI)")
        
        # 2. Vérifier l'indentation des scripts
        script_blocks = re.findall(r'script:\s*\n((?:\s*-.*\n)*)', content, re.MULTILINE)
        for i, block in enumerate(script_blocks):
            if not block.strip():
                issues.append(f"❌ Bloc script {i+1} vide")
            elif not block.startswith('    -'):
                issues.append(f"❌ Bloc script {i+1} mal indenté")
        
        # 3. Vérifier la structure générale
        required_sections = ['stages:', 'build:', 'test:']
        for section in required_sections:
            if section not in content:
                issues.append(f"❌ Section manquante: {section}")
        
        # 4. Vérifier les caractères problématiques
        if '\t' in content:
            issues.append("❌ Tabulations détectées (utiliser des espaces)")
        
        # 5. Vérifier les blocs multi-lignes
        multiline_blocks = re.findall(r'- \|\s*\n(.*?)(?=\n\s*- |\n[a-z]|\nstages:|\Z)', content, re.DOTALL)
        for i, block in enumerate(multiline_blocks):
            if 'cat << EOF' in block or 'EOF' in block:
                issues.append(f"❌ Bloc multi-ligne {i+1} contient des constructions bash problématiques")
        
        if issues:
            print(f"⚠️ {len(issues)} problème(s) détecté(s) :")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("✅ Aucun problème de syntaxe détecté")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la validation : {e}")
        return False

def show_structure():
    """Affiche la structure du fichier"""
    gitlab_file = Path('.gitlab-ci.yml')
    
    try:
        with open(gitlab_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n📋 STRUCTURE DU FICHIER :")
        print("-" * 40)
        
        # Extraire les sections principales
        sections = re.findall(r'^([a-zA-Z_][a-zA-Z0-9_]*):(?:\s*&.*)?$', content, re.MULTILINE)
        for section in sections:
            print(f"  ✓ {section}")
        
        # Compter les lignes
        lines = content.split('\n')
        print(f"\n📊 Statistiques :")
        print(f"  • Lignes totales : {len(lines)}")
        print(f"  • Lignes non vides : {len([l for l in lines if l.strip()])}")
        print(f"  • Sections : {len(sections)}")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")

def main():
    print("🔍 VALIDATION FINALE GITLAB-CI.YML")
    print("=" * 50)
    
    is_valid = validate_gitlab_ci_syntax()
    show_structure()
    
    print("\n" + "=" * 50)
    if is_valid:
        print("✅ FICHIER VALIDE - Prêt pour GitLab !")
        print("🚀 Vous pouvez maintenant pusher en toute confiance")
    else:
        print("❌ FICHIER INVALIDE - Corrections nécessaires")
    
    print("\n💡 RAPPEL :")
    print("• GitLab CI n'aime pas les blocs 'cat << EOF'")
    print("• Utiliser des listes simples avec echo au lieu de heredoc")
    print("• Vérifier l'indentation (espaces, pas de tabs)")

if __name__ == "__main__":
    main()
