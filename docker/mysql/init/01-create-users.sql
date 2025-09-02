-- MySQL initialization script for DataAlign v2.0
-- This script runs automatically when MySQL container starts for the first time

-- Create additional users for different environments
CREATE USER IF NOT EXISTS 'dataalign_dev'@'%' IDENTIFIED BY 'dev123';
CREATE USER IF NOT EXISTS 'dataalign_test'@'%' IDENTIFIED BY 'test123';
CREATE USER IF NOT EXISTS 'dataalign_readonly'@'%' IDENTIFIED BY 'readonly123';
CREATE USER IF NOT EXISTS 'admin_user'@'%' IDENTIFIED BY 'admin456';

-- Create databases for different environments
CREATE DATABASE IF NOT EXISTS dataalign_dev;
CREATE DATABASE IF NOT EXISTS dataalign_test;

-- Grant permissions to main application user
GRANT ALL PRIVILEGES ON dataalign.* TO 'dataalign'@'%';

-- Grant permissions to development user
GRANT ALL PRIVILEGES ON dataalign_dev.* TO 'dataalign_dev'@'%';

-- Grant permissions to test user
GRANT ALL PRIVILEGES ON dataalign_test.* TO 'dataalign_test'@'%';

-- Grant read-only permissions to readonly user
GRANT SELECT ON dataalign.* TO 'dataalign_readonly'@'%';
GRANT SELECT ON dataalign_dev.* TO 'dataalign_readonly'@'%';
GRANT SELECT ON dataalign_test.* TO 'dataalign_readonly'@'%';

-- Grant admin permissions to admin user
GRANT ALL PRIVILEGES ON *.* TO 'admin_user'@'%' WITH GRANT OPTION;

-- Flush privileges to apply changes
FLUSH PRIVILEGES;

-- Show created users (for verification in logs)
SELECT User, Host FROM mysql.user WHERE User LIKE 'dataalign%' OR User = 'admin_user';
