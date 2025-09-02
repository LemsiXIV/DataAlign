#!/usr/bin/env python3
"""
Test GPT-4 automatic delimiter detection and structure fixing
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add app to path
sys.path.append('app')

from dotenv import load_dotenv
load_dotenv()

def create_test_files():
    """Create test files with different delimiter issues"""
    
    os.makedirs("temp", exist_ok=True)
    
    # Create semicolon-separated CSV (French style)
    semicolon_data = """Id;Nom complet;Intitulé du poste;Nom de la société;Adresse e-mail
001;Jean Dupont;Développeur;TechCorp;jean@techcorp.fr
002;Marie Martin;Chef de projet;InnovSA;marie@innovsa.fr
003;Pierre Durand;Analyste;DataCorp;pierre@datacorp.fr"""
    
    with open("temp/test_semicolon.csv", "w", encoding="utf-8") as f:
        f.write(semicolon_data)
    
    # Create tab-separated CSV
    tab_data = """Id\tNom complet\tIntitulé du poste\tNom de la société\tAdresse e-mail
001\tJean Dupont\tDéveloppeur\tTechCorp\tjean@techcorp.fr
002\tMarie Martin\tChef de projet\tInnovSA\tmarie@innovsa.fr
003\tPierre Durand\tAnalyste\tDataCorp\tpierre@datacorp.fr"""
    
    with open("temp/test_tab.csv", "w", encoding="utf-8") as f:
        f.write(tab_data)
    
    print("✅ Fichiers de test créés:")
    print("   - temp/test_semicolon.csv (délimiteur point-virgule)")
    print("   - temp/test_tab.csv (délimiteur tabulation)")

def test_standard_pandas_reading():
    """Test how pandas reads these files by default"""
    
    print("\n📊 Test de lecture pandas standard:")
    print("=" * 45)
    
    # Test semicolon file
    try:
        df_semi = pd.read_csv("temp/test_semicolon.csv")
        print(f"🔴 Fichier point-virgule - Colonnes détectées: {len(df_semi.columns)}")
        print(f"   Noms des colonnes: {list(df_semi.columns)}")
        if len(df_semi.columns) == 1:
            print("   ❌ PROBLÈME: Toutes les colonnes sont fusionnées!")
    except Exception as e:
        print(f"❌ Erreur lecture semicolon: {e}")
    
    # Test tab file
    try:
        df_tab = pd.read_csv("temp/test_tab.csv")
        print(f"🔴 Fichier tabulation - Colonnes détectées: {len(df_tab.columns)}")
        print(f"   Noms des colonnes: {list(df_tab.columns)}")
        if len(df_tab.columns) == 1:
            print("   ❌ PROBLÈME: Toutes les colonnes sont fusionnées!")
    except Exception as e:
        print(f"❌ Erreur lecture tab: {e}")

def test_gpt_structure_analysis():
    """Test GPT-4 structure analysis and fixing"""
    
    print("\n🤖 Test GPT-4 - Analyse et correction automatique:")
    print("=" * 55)
    
    try:
        from app.services.gpt_data_processor import GPTDataProcessor
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your_openai_api_key_here':
            print("⚠️  OpenAI API key non configuré - test GPT impossible")
            return False
        
        processor = GPTDataProcessor()
        
        # Test semicolon file
        print("\n🔍 Analyse du fichier point-virgule:")
        analysis_semi = processor.analyze_and_fix_file_structure("temp/test_semicolon.csv")
        print(f"   Délimiteur détecté: '{analysis_semi.get('detected_delimiter', 'N/A')}'")
        print(f"   Problèmes identifiés: {analysis_semi.get('structure_issues', [])}")
        
        # Fix and test
        fixed_df_semi = processor.fix_file_with_gpt_analysis("temp/test_semicolon.csv")
        print(f"   ✅ Après correction: {len(fixed_df_semi.columns)} colonnes")
        print(f"   Colonnes: {list(fixed_df_semi.columns)}")
        
        # Test tab file
        print("\n🔍 Analyse du fichier tabulation:")
        analysis_tab = processor.analyze_and_fix_file_structure("temp/test_tab.csv")
        print(f"   Délimiteur détecté: '{analysis_tab.get('detected_delimiter', 'N/A')}'")
        
        fixed_df_tab = processor.fix_file_with_gpt_analysis("temp/test_tab.csv")
        print(f"   ✅ Après correction: {len(fixed_df_tab.columns)} colonnes")
        print(f"   Colonnes: {list(fixed_df_tab.columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur GPT: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration like in the real application"""
    
    print("\n🎯 Test d'intégration complète:")
    print("=" * 35)
    
    try:
        from app.services.gpt_data_processor import GPTDataProcessor
        
        processor = GPTDataProcessor()
        
        # Simulate the logic from fichiers.py
        df = pd.read_csv("temp/test_semicolon.csv")
        print(f"📁 Avant GPT: {len(df.columns)} colonnes")
        print(f"   Première colonne: '{df.columns[0]}'")
        
        # Check if structure issue exists (like in the route)
        if len(df.columns) == 1 and ';' in str(df.columns[0]):
            print("🔍 GPT-4 détecte un problème de structure...")
            df_fixed = processor.fix_file_with_gpt_analysis("temp/test_semicolon.csv")
            print(f"✅ Après GPT: {len(df_fixed.columns)} colonnes")
            print(f"   Colonnes séparées: {list(df_fixed.columns)}")
            
            return len(df_fixed.columns) > 1
        else:
            print("✅ Aucun problème de structure détecté")
            return True
            
    except Exception as e:
        print(f"❌ Erreur intégration: {e}")
        return False

def cleanup():
    """Clean up test files"""
    try:
        os.remove("temp/test_semicolon.csv")
        os.remove("temp/test_tab.csv")
        print("\n🧹 Fichiers de test supprimés")
    except:
        pass

if __name__ == "__main__":
    print("🧪 Test GPT-4 - Détection automatique des délimiteurs")
    print("=" * 60)
    
    try:
        # Create test files
        create_test_files()
        
        # Test standard pandas behavior
        test_standard_pandas_reading()
        
        # Test GPT analysis
        gpt_success = test_gpt_structure_analysis()
        
        # Test integration
        integration_success = test_integration()
        
        print(f"\n🏁 Résultats finaux:")
        print(f"   GPT-4 Analysis: {'✅ SUCCÈS' if gpt_success else '❌ ÉCHEC'}")
        print(f"   Intégration: {'✅ SUCCÈS' if integration_success else '❌ ÉCHEC'}")
        
        if gpt_success and integration_success:
            print("\n🎉 GPT-4 peut maintenant détecter et corriger automatiquement")
            print("   les problèmes de délimiteurs dans vos fichiers!")
            print("\n📝 Pour utiliser:")
            print("   1. Uploadez vos fichiers dans Fast Test")
            print("   2. ✅ Activez 'Amélioration GPT-4'") 
            print("   3. GPT-4 détectera et corrigera automatiquement les problèmes")
        else:
            print("\n❌ Certains tests ont échoué - vérifiez la configuration")
            
    finally:
        cleanup()
