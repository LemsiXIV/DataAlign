#!/usr/bin/env python3
"""
Système de migration automatique pour DataAlign
Détecte les changements de modèles et applique les migrations automatiquement
"""

import os
import hashlib
import json
import time
from datetime import datetime
from sqlalchemy import inspect, text
from flask import current_app
from app import db
from app.models.logs import LogExecution

class AutoMigrationManager:
    def __init__(self, app=None):
        self.app = app
        self.migrations_dir = "migrations/auto"
        self.schema_file = "schema_checksum.json"
        
    def init_app(self, app):
        self.app = app
        
    def ensure_migrations_dir(self):
        """Créer le dossier de migrations s'il n'existe pas"""
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
            
    def get_current_schema_hash(self):
        """Obtenir le hash du schéma actuel de la base de données"""
        inspector = inspect(db.engine)
        schema_info = {}
        
        # Récupérer les informations de toutes les tables
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            
            schema_info[table_name] = {
                'columns': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable'],
                        'default': str(col['default']) if col['default'] else None
                    }
                    for col in columns
                ],
                'indexes': [
                    {
                        'name': idx['name'],
                        'columns': idx['column_names'],
                        'unique': idx['unique']
                    }
                    for idx in indexes
                ],
                'foreign_keys': [
                    {
                        'constrained_columns': fk['constrained_columns'],
                        'referred_table': fk['referred_table'],
                        'referred_columns': fk['referred_columns']
                    }
                    for fk in foreign_keys
                ]
            }
        
        # Créer un hash du schéma
        schema_str = json.dumps(schema_info, sort_keys=True)
        return hashlib.md5(schema_str.encode()).hexdigest()
    
    def load_stored_schema_hash(self):
        """Charger le hash du schéma stocké"""
        if os.path.exists(self.schema_file):
            try:
                with open(self.schema_file, 'r') as f:
                    data = json.load(f)
                    return data.get('schema_hash'), data.get('last_check')
            except:
                return None, None
        return None, None
    
    def save_schema_hash(self, schema_hash):
        """Sauvegarder le hash du schéma actuel"""
        data = {
            'schema_hash': schema_hash,
            'last_check': datetime.now().isoformat(),
            'app_version': '1.0.0'  # Vous pouvez ajuster cela selon vos besoins
        }
        
        with open(self.schema_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def detect_schema_changes(self):
        """Détecter les changements dans le schéma"""
        current_hash = self.get_current_schema_hash()
        stored_hash, last_check = self.load_stored_schema_hash()
        
        return {
            'has_changes': current_hash != stored_hash,
            'current_hash': current_hash,
            'stored_hash': stored_hash,
            'last_check': last_check
        }
    
    def create_tables_if_not_exist(self):
        """Créer les tables qui n'existent pas"""
        try:
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # Obtenir toutes les tables définies dans les modèles
            metadata_tables = db.metadata.tables.keys()
            
            new_tables = []
            for table_name in metadata_tables:
                if table_name not in existing_tables:
                    new_tables.append(table_name)
            
            if new_tables:
                print(f"Création de nouvelles tables: {new_tables}")
                db.create_all()
                return new_tables
            
            return []
            
        except Exception as e:
            print(f"Erreur lors de la création des tables: {e}")
            raise
    
    def log_migration_result(self, migration_type, status, message, details=None, execution_time_ms=None):
        """Enregistrer le résultat de la migration dans les logs"""
        try:
            full_message = f"Migration automatique - {migration_type}:\n{message}"
            if details:
                full_message += f"\nDétails:\n{details}"
            
            # Log dans la table logs_execution pour compatibilité
            log_entry = LogExecution(
                projet_id=None,  # Migration système
                statut="succès" if status == "SUCCESS" else "échec",
                message=full_message
            )
            
            db.session.add(log_entry)
            
            # Essayer d'importer et utiliser MigrationHistory si disponible
            try:
                from app.models.migration_history import MigrationHistory
                
                migration_history = MigrationHistory.log_migration(
                    migration_name=f"auto_migration_{int(time.time())}",
                    migration_type=migration_type.lower().replace(' ', '_'),
                    status=status,
                    message=message,
                    details=details,
                    execution_time_ms=execution_time_ms
                )
            except ImportError:
                # MigrationHistory n'est pas encore disponible (première migration)
                pass
            
            db.session.commit()
            
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du log: {e}")
            # Ne pas faire échouer la migration pour un problème de log
            try:
                db.session.rollback()
            except:
                pass
    
    def run_auto_migration(self):
        """Exécuter la migration automatique"""
        try:
            self.ensure_migrations_dir()
            
            print("=== Démarrage de la migration automatique ===")
            
            # Étape 1: Créer les tables manquantes
            new_tables = self.create_tables_if_not_exist()
            if new_tables:
                message = f"Nouvelles tables créées: {', '.join(new_tables)}"
                print(f"✅ {message}")
                self.log_migration_result("Création de tables", "succès", message)
            
            # Étape 2: Détecter les changements de schéma
            changes = self.detect_schema_changes()
            
            if changes['has_changes']:
                print("📊 Changements détectés dans le schéma de base de données")
                
                # Appliquer des migrations spécifiques connues
                migration_applied = self.apply_known_migrations()
                
                if migration_applied:
                    # Mettre à jour le hash du schéma
                    self.save_schema_hash(changes['current_hash'])
                    
                    message = "Migrations automatiques appliquées avec succès"
                    print(f"✅ {message}")
                    self.log_migration_result("Mise à jour de schéma", "succès", message, 
                                            f"Hash précédent: {changes['stored_hash']}\nNouveau hash: {changes['current_hash']}")
                else:
                    print("ℹ️ Aucune migration automatique applicable trouvée")
                    # Sauvegarder quand même le nouveau hash pour éviter les vérifications répétées
                    self.save_schema_hash(changes['current_hash'])
            else:
                print("✅ Aucun changement de schéma détecté")
                
                # Mettre à jour la date de dernière vérification
                if changes['stored_hash']:
                    self.save_schema_hash(changes['current_hash'])
            
            print("=== Migration automatique terminée ===")
            
        except Exception as e:
            error_message = f"Erreur lors de la migration automatique: {str(e)}"
            print(f"❌ {error_message}")
            self.log_migration_result("Erreur de migration", "échec", error_message)
            raise
    
    def apply_known_migrations(self):
        """Appliquer les migrations connues et courantes"""
        migrations_applied = False
        
        try:
            # Migration 1: S'assurer que logs_execution.projet_id peut être NULL
            if self.ensure_logs_projet_id_nullable():
                migrations_applied = True
                
            # Migration 2: Ajouter des indexes si nécessaire
            if self.ensure_performance_indexes():
                migrations_applied = True
                
            # Migration 3: Vérifier et ajouter les colonnes manquantes dans fichiers_generes
            if self.check_missing_columns_fichier_genere():
                print("🔄 Colonnes manquantes détectées dans fichiers_generes")
                sql_commands = self.get_fichier_genere_migration_sql()
                
                if sql_commands:
                    try:
                        for sql in sql_commands:
                            if sql.strip():
                                print(f"   → Exécution: {sql}")
                                db.session.execute(text(sql))
                        
                        db.session.commit()
                        migrations_applied = True
                        
                        self.log_migration_result(
                            migration_type="SCHEMA_UPDATE",
                            status="SUCCESS",
                            message="Colonnes manquantes ajoutées à fichiers_generes",
                            details=f"Commandes SQL exécutées: {'; '.join(sql_commands)}"
                        )
                        print("✅ Colonnes ajoutées avec succès à fichiers_generes")
                        
                    except Exception as e:
                        print(f"❌ Erreur lors de l'ajout des colonnes: {e}")
                        db.session.rollback()
                        self.log_migration_result(
                            migration_type="SCHEMA_UPDATE", 
                            status="FAILED",
                            message=f"Échec de l'ajout des colonnes à fichiers_generes: {str(e)}"
                        )
            
            # Vous pouvez ajouter d'autres migrations ici
            
        except Exception as e:
            print(f"Erreur lors de l'application des migrations: {e}")
            raise
            
        return migrations_applied
    
    def ensure_logs_projet_id_nullable(self):
        """S'assurer que la colonne projet_id dans logs_execution peut être NULL"""
        try:
            with db.engine.begin() as connection:
                # Vérifier si la colonne est déjà nullable
                result = connection.execute(text("""
                    SELECT IS_NULLABLE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'logs_execution' 
                    AND COLUMN_NAME = 'projet_id'
                """))
                
                row = result.fetchone()
                if row and row[0] == 'NO':
                    # La colonne n'est pas nullable, la modifier
                    connection.execute(text("""
                        ALTER TABLE logs_execution 
                        MODIFY COLUMN projet_id INT NULL
                    """))
                    print("✅ Migration: logs_execution.projet_id maintenant nullable")
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Migration logs_execution.projet_id: {e}")
            return False
    
    def ensure_performance_indexes(self):
        """Ajouter des indexes pour améliorer les performances"""
        indexes_added = False
        
        try:
            with db.engine.begin() as connection:
                # Index sur logs_execution.date_execution pour les requêtes de logs
                try:
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_logs_date_execution 
                        ON logs_execution(date_execution)
                    """))
                    print("✅ Index créé: idx_logs_date_execution")
                    indexes_added = True
                except:
                    pass  # Index peut déjà exister
                
                # Index sur projets.nom_projet pour les recherches
                try:
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_projets_nom 
                        ON projets(nom_projet)
                    """))
                    print("✅ Index créé: idx_projets_nom")
                    indexes_added = True
                except:
                    pass
                
                # Index sur projets.date_creation pour le tri
                try:
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_projets_date_creation 
                        ON projets(date_creation)
                    """))
                    print("✅ Index créé: idx_projets_date_creation")
                    indexes_added = True
                except:
                    pass
                    
        except Exception as e:
            print(f"Erreur lors de la création des indexes: {e}")
            
        return indexes_added
    
    def check_missing_columns_fichier_genere(self):
        """Vérifier s'il manque des colonnes dans la table fichiers_generes"""
        try:
            inspector = inspect(db.engine)
            columns = inspector.get_columns('fichiers_generes')
            existing_columns = [col['name'] for col in columns]
            
            # Colonnes attendues selon le modèle
            expected_columns = ['id', 'projet_id', 'nom_fichier_excel', 'nom_fichier_pdf', 
                              'nom_fichier_graphe', 'chemin_archive', 'date_execution']
            
            missing_columns = [col for col in expected_columns if col not in existing_columns]
            
            return len(missing_columns) > 0
            
        except Exception as e:
            print(f"Erreur lors de la vérification des colonnes FichierGenere: {e}")
            return False
    
    def get_fichier_genere_migration_sql(self):
        """Obtenir les commandes SQL pour ajouter les colonnes manquantes à fichiers_generes"""
        try:
            inspector = inspect(db.engine)
            columns = inspector.get_columns('fichiers_generes')
            existing_columns = [col['name'] for col in columns]
            
            sql_commands = []
            
            if 'nom_fichier_pdf' not in existing_columns:
                sql_commands.append("ALTER TABLE fichiers_generes ADD COLUMN nom_fichier_pdf VARCHAR(255) NULL")
            
            if 'date_execution' not in existing_columns:
                sql_commands.append("ALTER TABLE fichiers_generes ADD COLUMN date_execution DATETIME NULL DEFAULT CURRENT_TIMESTAMP")
            
            return sql_commands
            
        except Exception as e:
            print(f"Erreur lors de la génération du SQL FichierGenere: {e}")
            return []

# Instance globale du gestionnaire de migration
migration_manager = AutoMigrationManager()

def init_auto_migration(app):
    """Initialiser le système de migration automatique"""
    migration_manager.init_app(app)
    
    # Exécuter la migration au démarrage de l'application
    with app.app_context():
        migration_manager.run_auto_migration()

def run_migration_check():
    """Fonction pour exécuter une vérification de migration manuellement"""
    return migration_manager.run_auto_migration()
