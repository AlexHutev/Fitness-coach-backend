-- FitnessCoach Database Setup Script
-- Run this in your MySQL client or MySQL Workbench

-- Create database
CREATE DATABASE IF NOT EXISTS fitness_coach_db;

-- Create user (change password if needed)
CREATE USER IF NOT EXISTS 'fitness_coach_user'@'localhost' IDENTIFIED BY 'FitnessCoach2024!';

-- Grant privileges
GRANT ALL PRIVILEGES ON fitness_coach_db.* TO 'fitness_coach_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Show databases to verify
SHOW DATABASES;

-- Show users to verify
SELECT User, Host FROM mysql.user WHERE User = 'fitness_coach_user';

-- Test the database
USE fitness_coach_db;
SELECT 'Database setup completed successfully!' as Status;
