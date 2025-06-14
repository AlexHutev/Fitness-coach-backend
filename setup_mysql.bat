@echo off
echo Setting up FitnessCoach Database...
echo.

echo Creating database and user...
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS fitness_coach_db;"
mysql -u root -p -e "CREATE USER IF NOT EXISTS 'fitness_coach_user'@'localhost' IDENTIFIED BY 'FitnessCoach2024!';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON fitness_coach_db.* TO 'fitness_coach_user'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"

echo.
echo Database setup completed!
echo Database: fitness_coach_db
echo User: fitness_coach_user
echo Password: FitnessCoach2024!
