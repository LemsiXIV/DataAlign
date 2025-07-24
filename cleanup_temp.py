#!/usr/bin/env python3
"""
Script de nettoyage automatique des fichiers temporaires
Supprime les fichiers dans le dossier temp/ plus anciens que 5 heures
Enregistre les actions dans la base de données
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Import des modèles Flask
from app import create_app, db
from app.models.logs import LogExecution

# Configuration
TEMP_DIR = "temp"
MAX_AGE_HOURS = 5
LOG_FILE = "cleanup.log"

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def cleanup_temp_files():
    """
    Supprime les fichiers temporaires plus anciens que MAX_AGE_HOURS heures
    et enregistre les actions dans la base de données
    """
    # Créer le contexte de l'application Flask
    app = create_app()
    
    with app.app_context():
        if not os.path.exists(TEMP_DIR):
            error_msg = f"Le dossier {TEMP_DIR} n'existe pas"
            logging.warning(error_msg)
            
            # Enregistrer dans la DB
            log_entry = LogExecution(
                projet_id=None,
                statut='échec',
                message=f"Nettoyage manuel: {error_msg}"
            )
            db.session.add(log_entry)
            db.session.commit()
            return
        
        current_time = time.time()
        cutoff_time = current_time - (MAX_AGE_HOURS * 3600)  # 5 heures en secondes
        
        deleted_count = 0
        total_size_deleted = 0
        deleted_files = []
        errors = []
        
        try:
            for filename in os.listdir(TEMP_DIR):
                file_path = os.path.join(TEMP_DIR, filename)
                
                # Vérifier que c'est bien un fichier
                if os.path.isfile(file_path):
                    # Obtenir le temps de modification du fichier
                    file_mtime = os.path.getmtime(file_path)
                    
                    # Si le fichier est plus ancien que 5 heures
                    if file_mtime < cutoff_time:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            total_size_deleted += file_size
                            
                            # Calculer l'âge du fichier
                            age_hours = (current_time - file_mtime) / 3600
                            
                            deleted_files.append({
                                'filename': filename,
                                'age_hours': age_hours,
                                'size': file_size
                            })
                            
                            logging.info(f"Supprimé: {filename} (âge: {age_hours:.1f}h, taille: {file_size} bytes)")
                            
                        except OSError as e:
                            error_msg = f"Erreur lors de la suppression de {filename}: {e}"
                            errors.append(error_msg)
                            logging.error(error_msg)
                    else:
                        # Calculer l'âge du fichier
                        age_hours = (current_time - file_mtime) / 3600
                        logging.debug(f"Conservé: {filename} (âge: {age_hours:.1f}h)")
        
        except OSError as e:
            error_msg = f"Erreur lors de l'accès au dossier {TEMP_DIR}: {e}"
            logging.error(error_msg)
            
            # Enregistrer l'erreur dans la DB
            log_entry = LogExecution(
                projet_id=None,
                statut='échec',
                message=f"Nettoyage manuel: {error_msg}"
            )
            db.session.add(log_entry)
            db.session.commit()
            return
        
        # Enregistrer le résultat dans la base de données
        if deleted_count > 0 or errors:
            size_mb = total_size_deleted / (1024 * 1024)
            
            # Créer le message détaillé
            summary_parts = []
            if deleted_count > 0:
                summary_parts.append(f"{deleted_count} fichiers supprimés ({size_mb:.2f} MB)")
                
                # Détail des fichiers supprimés (limiter à 10 pour éviter des messages trop longs)
                files_detail = []
                for i, f in enumerate(deleted_files[:10]):
                    files_detail.append(f"- {f['filename']} (âge: {f['age_hours']:.1f}h, {f['size']} bytes)")
                
                if len(deleted_files) > 10:
                    files_detail.append(f"... et {len(deleted_files) - 10} autres fichiers")
                
                if files_detail:
                    summary_parts.append("Fichiers supprimés:\n" + "\n".join(files_detail))
            
            if errors:
                summary_parts.append(f"{len(errors)} erreurs rencontrées:\n" + "\n".join(errors[:5]))
                if len(errors) > 5:
                    summary_parts.append(f"... et {len(errors) - 5} autres erreurs")
            
            message = "Nettoyage manuel des fichiers temporaires:\n" + "\n".join(summary_parts)
            
            # Déterminer le statut
            statut = 'succès' if not errors else ('échec' if deleted_count == 0 else 'succès')
            
            log_entry = LogExecution(
                projet_id=None,
                statut=statut,
                message=message
            )
            db.session.add(log_entry)
            db.session.commit()
            
            logging.info(f"Nettoyage terminé: {deleted_count} fichiers supprimés, {size_mb:.2f} MB libérés")
        else:
            # Aucun fichier à supprimer
            log_entry = LogExecution(
                projet_id=None,
                statut='succès',
                message="Nettoyage manuel: Aucun fichier temporaire à supprimer"
            )
            db.session.add(log_entry)
            db.session.commit()
            
            logging.info("Aucun fichier à supprimer")

def main():
    """Fonction principale"""
    logging.info("=== Début du nettoyage automatique des fichiers temporaires ===")
    cleanup_temp_files()
    logging.info("=== Fin du nettoyage ===")

if __name__ == "__main__":
    main()
