#!/usr/bin/env python3
"""
Validateur YAML simple sans dépendances
"""
import re
from pathlib import Path

def check_yaml_basic_syntax():
    """Vérifie la syntaxe YAML de base"""
    gitlab_file = Path('.gitlab-ci.yml')
    
    try:
        with open(gitlab_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"📄 Fichier: {len(lines)} lignes")
        
        errors = []
        
        for i, line in enumerate(lines, 1):
            line_content = line.rstrip('\n\r')
            
            # Vérifications basiques
            if '\t' in line_content:
                errors.append(f"Ligne {i}: Tabulation détectée (utiliser des espaces)")
            
            # Vérifier structure clé: valeur
            if ':' in line_content and not line_content.strip().startswith('#'):
                # Si c'est une clé au niveau racine
                if not line_content.startswith(' ') and not line_content.strip().startswith('-'):
                    if not line_content.strip().endswith(':'):
                        # Doit être une clé avec valeur
                        if '=' not in line_content and not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*:\s*.+', line_content.strip()):
                            errors.append(f"Ligne {i}: Syntaxe clé:valeur incorrecte - '{line_content.strip()}'")
            
            # Vérifier indentation liste
            if line_content.strip().startswith('-'):
                stripped = line_content.lstrip()
                indent = len(line_content) - len(stripped)
                if indent % 2 != 0:
                    errors.append(f"Ligne {i}: Indentation impaire pour liste (doit être multiple de 2)")
        
        if errors:
            print("❌ ERREURS DÉTECTÉES:")
            for error in errors[:5]:  # Limiter à 5 erreurs
                print(f"  {error}")
            if len(errors) > 5:
                print(f"  ... et {len(errors) - 5} autres erreurs")
            return False
        else:
            print("✅ Syntaxe YAML basique correcte")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la lecture: {e}")
        return False

def check_gitlab_structure():
    """Vérifie la structure GitLab CI"""
    gitlab_file = Path('.gitlab-ci.yml')
    
    try:
        with open(gitlab_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_sections = ['stages:', 'build:', 'test:']
        missing = []
        
        for section in required_sections:
            if section not in content:
                missing.append(section)
        
        if missing:
            print(f"⚠️ Sections manquantes: {missing}")
            return False
        else:
            print("✅ Structure GitLab CI correcte")
            return True
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("🔍 VALIDATION YAML GITLAB-CI")
    print("=" * 40)
    
    syntax_ok = check_yaml_basic_syntax()
    structure_ok = check_gitlab_structure()
    
    print("\n" + "=" * 40)
    if syntax_ok and structure_ok:
        print("✅ FICHIER VALIDE - Prêt pour GitLab!")
        print("🚀 Le pipeline devrait maintenant fonctionner")
    else:
        print("❌ PROBLÈMES DÉTECTÉS")
        print("🔧 Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()
