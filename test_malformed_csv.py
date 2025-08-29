#!/usr/bin/env python3
"""
Script de test pour vérifier la gestion des fichiers CSV malformés
"""
import sys
import os

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.encoding_utils import safe_read_csv

def test_malformed_csv():
    """Test de la lecture de fichiers CSV malformés"""
    print("=== TEST DE LECTURE CSV MALFORMEES ===")
    
    # Créer des fichiers de test avec différents problèmes
    os.makedirs("temp", exist_ok=True)
    
    # 1. Fichier avec nombre de colonnes inconsistant
    malformed_content = """nom,age,ville,pays
Pierre,25,Montreal,Canada
Marie,30,Quebec
Jean,35,Toronto,Canada,extra,data
Alice,28,Paris,France"""
    
    with open("temp/malformed.csv", "w", encoding='utf-8') as f:
        f.write(malformed_content)
    
    # 2. Fichier avec virgules dans les données (non échappées)
    csv_with_commas = """nom,description,prix
Produit A,"Description avec, des virgules",25.50
Produit B,Description normale,30.00
Produit C,"Autre description, avec virgules, multiples",45.75"""
    
    with open("temp/with_commas.csv", "w", encoding='utf-8') as f:
        f.write(csv_with_commas)
    
    # 3. Fichier avec séparateur point-virgule
    semicolon_csv = """nom;age;ville
Pierre;25;Montreal
Marie;30;Quebec
Jean;35;Toronto"""
    
    with open("temp/semicolon.csv", "w", encoding='utf-8') as f:
        f.write(semicolon_csv)
    
    test_files = [
        ("temp/malformed.csv", "Fichier avec colonnes inconsistantes"),
        ("temp/with_commas.csv", "Fichier avec virgules dans les données"),
        ("temp/semicolon.csv", "Fichier avec séparateur point-virgule")
    ]
    
    for file_path, description in test_files:
        try:
            print(f"\n--- {description} ---")
            df = safe_read_csv(file_path)
            print(f"✅ Lecture réussie: {len(df)} lignes, {len(df.columns)} colonnes")
            print(f"Colonnes: {list(df.columns)}")
            print(f"Aperçu des données:")
            print(df.head())
            
        except Exception as e:
            print(f"❌ Erreur lors de la lecture de {file_path}: {e}")
            import traceback
            traceback.print_exc()
    
    # Nettoyer les fichiers de test
    for file_path, _ in test_files:
        if os.path.exists(file_path):
            os.remove(file_path)
    
    print("\n=== FIN DES TESTS ===")

if __name__ == "__main__":
    test_malformed_csv()
