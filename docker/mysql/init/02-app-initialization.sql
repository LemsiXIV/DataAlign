-- DataAlign application initialization
-- This script creates application-specific data and configurations

USE dataalign;

-- Create a sample configuration table for environment settings
CREATE TABLE IF NOT EXISTS app_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(255) NOT NULL UNIQUE,
    config_value TEXT,
    environment ENUM('development', 'staging', 'production') DEFAULT 'development',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default configuration values
INSERT IGNORE INTO app_config (config_key, config_value, environment) VALUES 
('app_name', 'DataAlign v2.0', 'development'),
('max_file_size', '50MB', 'development'),
('session_timeout', '3600', 'development'),
('auto_pdf_generation', 'true', 'development'),
('debug_mode', 'true', 'development'),
('max_comparison_rows', '50000', 'development');

-- Create system status table for health checks
CREATE TABLE IF NOT EXISTS system_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    status ENUM('running', 'stopped', 'error') DEFAULT 'running',
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    details TEXT
);

-- Insert initial system status
INSERT IGNORE INTO system_status (service_name, status, details) VALUES 
('mysql', 'running', 'Database initialized successfully'),
('flask_app', 'running', 'Application ready to start'),
('file_processor', 'running', 'File processing service ready');

-- Show initialization summary
SELECT 'DataAlign MySQL initialization completed successfully' AS status;
SELECT COUNT(*) AS config_entries FROM app_config;
SELECT COUNT(*) AS system_services FROM system_status;
