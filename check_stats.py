#!/usr/bin/env python3
"""
Script pour vérifier la structure de la table statistiques_ecarts
"""
import pymysql

def check_stats_table():
    """Vérifier la structure de la table statistiques_ecarts"""
    
    connection = pymysql.connect(
        host='localhost',
        user='DataAlign',
        password='DataAlign',
        database='DataAlign',
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # Vérifier la structure de la table
            cursor.execute("DESCRIBE statistiques_ecarts")
            columns = cursor.fetchall()
            
            print("📋 Structure de la table 'statistiques_ecarts':")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
            
            # Vérifier le contenu pour le projet 3
            cursor.execute("SELECT * FROM statistiques_ecarts WHERE projet_id = 3")
            stats = cursor.fetchall()
            
            print(f"\n📊 Statistiques pour projet ID 3:")
            if stats:
                for stat in stats:
                    print(f"  Enregistrement: {stat}")
            else:
                print("  Aucune statistique trouvée pour le projet 3")
                
            # Lister tous les projets avec des statistiques
            cursor.execute("SELECT DISTINCT projet_id FROM statistiques_ecarts")
            projets_avec_stats = cursor.fetchall()
            
            print(f"\n📈 Projets avec des statistiques:")
            for projet in projets_avec_stats:
                print(f"  - Projet ID: {projet[0]}")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    check_stats_table()
