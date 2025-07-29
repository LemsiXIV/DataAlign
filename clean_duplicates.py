#!/usr/bin/env python3
"""
Script pour nettoyer les doublons dans la table fichiers_generes
"""
from app import create_app, db
from app.models.fichier_genere import FichierGenere
from app.models import Projet
from datetime import datetime, timedelta

def clean_duplicates():
    """Nettoyer les doublons et regrouper les fichiers du même traitement"""
    app = create_app()
    
    with app.app_context():
        try:
            # Récupérer tous les projets
            projets = Projet.query.all()
            
            for projet in projets:
                print(f"🔍 Nettoyage des fichiers générés pour le projet: {projet.nom_projet}")
                
                # Récupérer tous les fichiers générés pour ce projet, triés par date
                fichiers = FichierGenere.query.filter_by(projet_id=projet.id).order_by(FichierGenere.date_execution.desc()).all()
                
                if len(fichiers) <= 1:
                    continue
                
                print(f"   📁 Trouvé {len(fichiers)} enregistrements")
                
                # Regrouper les fichiers par proximité temporelle (5 minutes)
                groupes = []
                for fichier in fichiers:
                    placed = False
                    for groupe in groupes:
                        # Si la différence de temps est inférieure à 5 minutes, ajouter au groupe
                        if abs((fichier.date_execution - groupe[0].date_execution).total_seconds()) < 300:  # 5 minutes
                            groupe.append(fichier)
                            placed = True
                            break
                    
                    if not placed:
                        groupes.append([fichier])
                
                print(f"   🗂️ Regroupé en {len(groupes)} traitements")
                
                # Pour chaque groupe, fusionner en un seul enregistrement
                for groupe in groupes:
                    if len(groupe) > 1:
                        # Garder le premier (plus récent) et fusionner les autres
                        principal = groupe[0]
                        
                        for i in range(1, len(groupe)):
                            fichier_a_fusionner = groupe[i]
                            
                            # Fusionner les informations
                            if fichier_a_fusionner.nom_fichier_excel and not principal.nom_fichier_excel:
                                principal.nom_fichier_excel = fichier_a_fusionner.nom_fichier_excel
                            
                            if fichier_a_fusionner.nom_fichier_pdf and not principal.nom_fichier_pdf:
                                principal.nom_fichier_pdf = fichier_a_fusionner.nom_fichier_pdf
                                
                            if fichier_a_fusionner.nom_fichier_graphe and not principal.nom_fichier_graphe:
                                principal.nom_fichier_graphe = fichier_a_fusionner.nom_fichier_graphe
                            
                            # Supprimer le doublon
                            db.session.delete(fichier_a_fusionner)
                            print(f"   🗑️ Supprimé doublon ID: {fichier_a_fusionner.id}")
                        
                        # Mettre à jour le nom du traitement principal
                        if not principal.nom_traitement_projet or principal.nom_traitement_projet.startswith('Traitement'):
                            principal.nom_traitement_projet = f"Traitement_{principal.date_execution.strftime('%Y%m%d_%H%M%S')}"
                        
                        print(f"   ✅ Fusionné en: {principal.nom_traitement_projet}")
                
                db.session.commit()
            
            print("✅ Nettoyage terminé avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage: {e}")
            db.session.rollback()

if __name__ == "__main__":
    clean_duplicates()
