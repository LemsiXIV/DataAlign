#!/usr/bin/env python3
"""
Script pour supprimer et recréer la table fichiers_generes avec le bon nom de colonne
"""
import pymysql

def recreate_table():
    """Supprimer et recréer la table fichiers_generes"""
    
    connection = pymysql.connect(
        host='localhost',
        user='DataAlign',
        password='DataAlign',
        database='DataAlign',
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # Supprimer l'ancienne table si elle existe
            cursor.execute("DROP TABLE IF EXISTS `fichiers_generes`")
            print("🗑️ Ancienne table supprimée")
            
            # Créer la nouvelle table avec le bon nom de colonne
            create_table_sql = """
            CREATE TABLE `fichiers_generes` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `projet_id` int(11) NOT NULL,
                `nom_traitement_projet` varchar(255) DEFAULT NULL,
                `nom_fichier_excel` varchar(255) DEFAULT NULL,
                `nom_fichier_pdf` varchar(255) DEFAULT NULL,
                `nom_fichier_graphe` varchar(255) DEFAULT NULL,
                `chemin_archive` varchar(255) DEFAULT NULL,
                `date_execution` datetime DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                KEY `fk_fichiers_generes_projet` (`projet_id`),
                CONSTRAINT `fk_fichiers_generes_projet` 
                    FOREIGN KEY (`projet_id`) 
                    REFERENCES `projets` (`id`) 
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(create_table_sql)
            print("✅ Nouvelle table 'fichiers_generes' créée avec succès!")
            
            # Vérifier la création
            cursor.execute("DESCRIBE fichiers_generes")
            columns = cursor.fetchall()
            
            print("📋 Structure de la nouvelle table 'fichiers_generes':")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
                
        connection.commit()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    recreate_table()
