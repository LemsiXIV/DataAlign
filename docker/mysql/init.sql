-- Script d'initialisation MySQL pour DataAlign
-- Ce script s'exécute automatiquement au premier démarrage

USE dataalign_dev;

-- Configuration pour DataAlign
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- Créer les tables de base si elles n'existent pas
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    reset_token VARCHAR(255) NULL,
    reset_token_expires DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    description TEXT,
    statut VARCHAR(50) DEFAULT 'nouveau',
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS logs_execution (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    niveau VARCHAR(20),
    message TEXT,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Insérer des utilisateurs de test
INSERT IGNORE INTO users (username, email, password_hash, is_admin) VALUES 
('testVikinn', 'admin@dataalign.com', 'scrypt:32768:8:1$vWJ4E6YaJHCKGOeJ$a9f55c8a7e8a6c9b4f3c8e7a2e5c9f4a8e6d7c3b9e8f5a7c4e2d8b6f9c3e7a5f', TRUE),
('testuser', 'user@dataalign.com', 'scrypt:32768:8:1$vWJ4E6YaJHCKGOeJ$7c8e9f3a6b5d2e8c4f7a9e3b8d6c5f2a9e7b4c8f6a3e5d7c9f2b8e4a6c7f5d8e', FALSE);

-- Insérer quelques projets de test
INSERT IGNORE INTO projets (nom, description, statut, user_id) VALUES
('Projet Test Admin', 'Projet de test pour administrateur', 'en_cours', 1),
('Projet Test User', 'Projet de test pour utilisateur normal', 'nouveau', 2),
('Analyse Données Q1', 'Analyse des données du premier trimestre', 'termine', 1);

-- Créer des indexes pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_reset_token ON users(reset_token);
CREATE INDEX IF NOT EXISTS idx_projets_user_id ON projets(user_id);
CREATE INDEX IF NOT EXISTS idx_projets_statut ON projets(statut);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs_execution(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs_execution(user_id);

-- Afficher le résultat
SELECT 'Base de données DataAlign initialisée avec succès!' as message;
