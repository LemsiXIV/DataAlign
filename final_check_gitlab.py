#!/usr/bin/env python3
"""
Test final du fichier .gitlab-ci.yml
"""
import re
from pathlib import Path

def final_check():
    """Test final du fichier"""
    gitlab_file = Path('.gitlab-ci.yml')
    
    with open(gitlab_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 TEST FINAL GITLAB-CI.YML")
    print("=" * 40)
    
    checks = []
    
    # 1. Syntaxe YAML basique
    lines = content.split('\n')
    has_tabs = any('\t' in line for line in lines)
    checks.append(("Pas de tabulations", not has_tabs))
    
    # 2. Structure requise
    required = ['stages:', 'build:', 'test:', 'script:']
    has_all = all(section in content for section in required)
    checks.append(("Structure GitLab CI complète", has_all))
    
    # 3. Emojis supprimés
    has_emojis = any(ord(c) > 127 for c in content)
    checks.append(("Emojis supprimés", not has_emojis))
    
    # 4. Indentation correcte
    bad_indent = False
    for line in lines:
        if line.strip().startswith('-'):
            indent = len(line) - len(line.lstrip())
            if indent % 2 != 0:
                bad_indent = True
                break
    checks.append(("Indentation correcte", not bad_indent))
    
    # 5. Jobs complets
    jobs_count = len(re.findall(r'^[a-zA-Z_][a-zA-Z0-9_]*:', content, re.MULTILINE))
    checks.append(("Jobs définis", jobs_count >= 5))
    
    # Affichage résultats
    passed = 0
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Score: {passed}/{len(checks)}")
    
    # Test spécifique GitLab
    print(f"\n📋 Détails:")
    print(f"  • Lignes: {len(lines)}")
    print(f"  • Jobs: {jobs_count}")
    print(f"  • Taille: {len(content)} caractères")
    
    if passed == len(checks):
        print(f"\n🎉 FICHIER PARFAIT!")
        print(f"✅ Prêt pour GitLab CI/CD")
        return True
    else:
        print(f"\n⚠️ Quelques problèmes restants")
        return False

if __name__ == "__main__":
    final_check()
