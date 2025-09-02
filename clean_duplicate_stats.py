#!/usr/bin/env python3
"""
Script pour nettoyer les entrées de statistiques dupliquées dans la table statistiques_ecarts
"""

import os
import sys

# Ajouter le répertoire parent au path pour importer l'app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.statistiques import StatistiqueEcart
from datetime import datetime
from sqlalchemy import func

def clean_duplicate_statistics():
    """Nettoie les entrées dupliquées de statistiques"""
    app = create_app()
    
    with app.app_context():
        print("🧹 Nettoyage des statistiques dupliquées...")
        
        # Récupérer toutes les statistiques groupées par projet et date (à la minute près)
        duplicate_groups = db.session.query(
            StatistiqueEcart.projet_id,
            func.date_format(StatistiqueEcart.date_execution, '%Y-%m-%d %H:%i').label('date_minute'),
            func.count(StatistiqueEcart.id).label('count')
        ).group_by(
            StatistiqueEcart.projet_id,
            func.date_format(StatistiqueEcart.date_execution, '%Y-%m-%d %H:%i')
        ).having(func.count(StatistiqueEcart.id) > 1).all()
        
        if not duplicate_groups:
            print("✅ Aucune statistique dupliquée trouvée.")
            return
        
        print(f"🔍 Trouvé {len(duplicate_groups)} groupes avec des doublons")
        
        total_removed = 0
        
        for group in duplicate_groups:
            projet_id = group.projet_id
            date_minute = group.date_minute
            count = group.count
            
            print(f"📊 Projet {projet_id}, minute {date_minute}: {count} entrées")
            
            # Récupérer toutes les entrées pour ce groupe
            entries = StatistiqueEcart.query.filter(
                StatistiqueEcart.projet_id == projet_id,
                func.date_format(StatistiqueEcart.date_execution, '%Y-%m-%d %H:%i') == date_minute
            ).order_by(StatistiqueEcart.date_execution.asc()).all()
            
            if len(entries) > 1:
                # Garder la première entrée, supprimer les autres
                entries_to_remove = entries[1:]
                
                for entry in entries_to_remove:
                    print(f"  🗑️ Suppression de l'entrée ID {entry.id} (date: {entry.date_execution})")
                    db.session.delete(entry)
                    total_removed += 1
        
        # Confirmer les suppressions
        if total_removed > 0:
            try:
                db.session.commit()
                print(f"✅ {total_removed} entrées dupliquées supprimées avec succès!")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erreur lors de la suppression: {e}")
        else:
            print("ℹ️ Aucune entrée à supprimer.")
        
        # Afficher les statistiques finales
        total_stats = StatistiqueEcart.query.count()
        print(f"📈 Total des statistiques restantes: {total_stats}")

if __name__ == "__main__":
    clean_duplicate_statistics()
