#!/usr/bin/env python3
"""
Validation YAML précise pour GitLab CI
"""
import re
from pathlib import Path

def validate_yaml_structure():
    """Validation précise de la structure YAML"""
    gitlab_file = Path('.gitlab-ci.yml')
    
    with open(gitlab_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 VALIDATION YAML PRÉCISE")
    print("=" * 40)
    
    errors = []
    warnings = []
    
    # Analyser ligne par ligne
    for i, line in enumerate(lines, 1):
        line_content = line.rstrip()
        
        # Vérifier structure clé: valeur au niveau racine
        if line_content and not line_content.startswith(' ') and not line_content.startswith('#'):
            if ':' in line_content:
                # C'est une clé de niveau racine
                if not line_content.endswith(':'):
                    # Doit avoir une valeur après :
                    parts = line_content.split(':', 1)
                    if len(parts) == 2 and not parts[1].strip():
                        errors.append(f"Ligne {i}: Clé sans valeur - '{line_content}'")
        
        # Vérifier les listes mal formées
        if line_content.strip().startswith('-'):
            # C'est un élément de liste
            stripped = line_content.lstrip()
            if not stripped.startswith('- '):
                if stripped.startswith('-') and len(stripped) > 1 and stripped[1] != ' ':
                    errors.append(f"Ligne {i}: Tiret sans espace - '{line_content.strip()}'")
        
        # Vérifier les problèmes de guillemets
        if '"' in line_content:
            # Compter les guillemets
            quote_count = line_content.count('"')
            if quote_count % 2 != 0:
                errors.append(f"Ligne {i}: Guillemets non fermés - '{line_content.strip()}'")
        
        # Vérifier indentation multiple de 2
        if line_content.startswith(' '):
            indent = len(line_content) - len(line_content.lstrip())
            if indent % 2 != 0:
                errors.append(f"Ligne {i}: Indentation impaire ({indent} espaces) - '{line_content.strip()}'")
    
    # Vérifier structure globale
    content = ''.join(lines)
    
    # Vérifier que chaque job a les clés requises
    job_pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*):(?:\s*#.*)?$'
    jobs = []
    
    for i, line in enumerate(lines):
        match = re.match(job_pattern, line)
        if match:
            job_name = match.group(1)
            if job_name not in ['stages', 'variables', 'cache', 'before_script']:
                jobs.append((job_name, i+1))
    
    print(f"📋 Jobs détectés: {[job[0] for job in jobs]}")
    
    # Vérifier chaque job
    for job_name, line_num in jobs:
        job_section = extract_job_content(lines, line_num-1)
        if 'stage:' not in job_section:
            warnings.append(f"Job {job_name}: 'stage:' manquant")
        if 'script:' not in job_section:
            errors.append(f"Job {job_name}: 'script:' manquant")
    
    # Affichage des résultats
    print(f"\n📊 RÉSULTATS:")
    print(f"✅ Lignes analysées: {len(lines)}")
    print(f"📋 Jobs trouvés: {len(jobs)}")
    print(f"❌ Erreurs: {len(errors)}")
    print(f"⚠️ Avertissements: {len(warnings)}")
    
    if errors:
        print(f"\n❌ ERREURS CRITIQUES:")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print(f"\n⚠️ AVERTISSEMENTS:")
        for warning in warnings[:5]:  # Limiter l'affichage
            print(f"  • {warning}")
    
    if not errors:
        print(f"\n✅ AUCUNE ERREUR DE SYNTAXE YAML")
        print(f"🚀 Le fichier devrait être accepté par GitLab")
        return True
    else:
        print(f"\n❌ CORRECTIONS NÉCESSAIRES")
        return False

def extract_job_content(lines, start_idx):
    """Extrait le contenu d'un job"""
    content = ""
    i = start_idx + 1
    
    while i < len(lines):
        line = lines[i]
        # Arrêter au prochain job (ligne sans indentation avec :)
        if line.strip() and not line.startswith(' ') and ':' in line:
            break
        content += line
        i += 1
    
    return content

def main():
    print("🎯 VALIDATION YAML GITLAB-CI PRÉCISE")
    print("🔍 Recherche d'erreurs de syntaxe YAML exactes")
    print("=" * 50)
    
    is_valid = validate_yaml_structure()
    
    if is_valid:
        print("\n🎉 VALIDATION RÉUSSIE!")
        print("✅ Votre .gitlab-ci.yml est syntaxiquement correct")
    else:
        print("\n🔧 VALIDATION ÉCHOUÉE")
        print("❌ Corrigez les erreurs listées ci-dessus")

if __name__ == "__main__":
    main()
