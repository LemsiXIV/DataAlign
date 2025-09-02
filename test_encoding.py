#!/usr/bin/env python3
"""
Script de test pour vérifier la gestion des encodages
"""
import sys
import os

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.encoding_utils import detect_csv_encoding, safe_read_csv

def test_encoding_detection():
    """Test de la détection d'encodage"""
    print("=== TEST DE DETECTION D'ENCODAGE ===")
    
    # Créer un fichier de test avec des caractères accentués
    test_content_utf8 = "nom,âge,ville\nPierre,25,Montréal\nMarie,30,Québec\n"
    test_content_latin1 = test_content_utf8.encode('utf-8').decode('utf-8').encode('latin-1')
    
    # Créer les fichiers de test
    os.makedirs("temp", exist_ok=True)
    
    # Fichier UTF-8
    with open("temp/test_utf8.csv", "w", encoding='utf-8') as f:
        f.write(test_content_utf8)
    
    # Fichier Latin-1
    with open("temp/test_latin1.csv", "wb") as f:
        f.write(test_content_latin1)
    
    try:
        # Test détection UTF-8
        encoding_utf8 = detect_csv_encoding("temp/test_utf8.csv")
        print(f"Encodage détecté pour fichier UTF-8: {encoding_utf8}")
        
        # Test détection Latin-1
        encoding_latin1 = detect_csv_encoding("temp/test_latin1.csv")
        print(f"Encodage détecté pour fichier Latin-1: {encoding_latin1}")
        
        # Test lecture sécurisée
        df_utf8 = safe_read_csv("temp/test_utf8.csv")
        print(f"Lecture UTF-8 réussie: {len(df_utf8)} lignes")
        print(f"Colonnes: {list(df_utf8.columns)}")
        
        df_latin1 = safe_read_csv("temp/test_latin1.csv")
        print(f"Lecture Latin-1 réussie: {len(df_latin1)} lignes")
        print(f"Colonnes: {list(df_latin1.columns)}")
        
        print("✅ Tous les tests d'encodage ont réussi!")
        
    except Exception as e:
        print(f"❌ Erreur dans les tests: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyer les fichiers de test
        for filename in ["temp/test_utf8.csv", "temp/test_latin1.csv"]:
            if os.path.exists(filename):
                os.remove(filename)

if __name__ == "__main__":
    test_encoding_detection()
