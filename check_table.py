#!/usr/bin/env python3
"""
Script pour vérifier la structure de la table fichiers_generes
"""
import pymysql

def check_table_structure():
    """Vérifier la structure actuelle de la table fichiers_generes"""
    
    connection = pymysql.connect(
        host='localhost',
        user='DataAlign',
        password='DataAlign',
        database='DataAlign',
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # Vérifier si la table existe
            cursor.execute("SHOW TABLES LIKE 'fichiers_generes'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                print("✅ La table 'fichiers_generes' existe")
                
                # Afficher la structure de la table
                cursor.execute("DESCRIBE fichiers_generes")
                columns = cursor.fetchall()
                
                print("📋 Structure actuelle de la table 'fichiers_generes':")
                for col in columns:
                    print(f"  - {col[0]} ({col[1]})")
                    
                # Vérifier spécifiquement la colonne problématique
                cursor.execute("SHOW COLUMNS FROM fichiers_generes LIKE '%traitement%'")
                traitement_cols = cursor.fetchall()
                
                if traitement_cols:
                    print("\n🔍 Colonnes contenant 'traitement':")
                    for col in traitement_cols:
                        print(f"  - {col[0]}")
                else:
                    print("\n❌ Aucune colonne contenant 'traitement' trouvée")
                    
            else:
                print("❌ La table 'fichiers_generes' n'existe pas")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    check_table_structure()
