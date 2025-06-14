# FitnessCoach Backend Setup Guide

## Database Setup Required

The FitnessCoach backend requires MySQL database setup. Here are the steps:

### Option 1: Manual Setup (Recommended)

1. **Open MySQL Workbench or MySQL Command Line Client**

2. **Connect as root user** (you'll need your MySQL root password)

3. **Run the following SQL commands:**
   ```sql
   -- Create database
   CREATE DATABASE IF NOT EXISTS fitness_coach_db;
   
   -- Create user
   CREATE USER IF NOT EXISTS 'fitness_coach_user'@'localhost' IDENTIFIED BY 'FitnessCoach2024!';
   
   -- Grant privileges
   GRANT ALL PRIVILEGES ON fitness_coach_db.* TO 'fitness_coach_user'@'localhost';
   
   -- Apply changes
   FLUSH PRIVILEGES;
   ```

4. **Verify the setup:**
   ```sql
   SHOW DATABASES;
   SELECT User, Host FROM mysql.user WHERE User = 'fitness_coach_user';
   ```

### Option 2: Using SQL Script

1. Run the provided SQL script:
   ```bash
   mysql -u root -p < setup_database.sql
   ```

### Option 3: If you don't have MySQL root password

If you can't access MySQL as root, you have a few options:

1. **Reset MySQL root password:**
   - Stop MySQL service
   - Start MySQL with `--skip-grant-tables`
   - Connect and reset password
   - Restart MySQL normally

2. **Use existing MySQL user:**
   - If you have another MySQL user with privileges
   - Modify the `.env` file with those credentials

3. **Use different database:**
   - SQLite (for development): Change database URL in `.env`
   - PostgreSQL: Install PostgreSQL and change settings

## After Database Setup

Once the database is ready:

1. **Test the connection:**
   ```bash
   python test_db_setup.py
   ```

2. **Initialize Alembic:**
   ```bash
   python -m alembic stamp head
   ```

3. **Create sample users:**
   ```bash
   python create_sample_users.py
   ```

4. **Start the API:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Alternative: SQLite for Development

If MySQL setup is problematic, you can use SQLite for development:

1. **Edit `.env` file:**
   ```env
   # Comment out MySQL settings
   # DB_HOST=localhost
   # DB_PORT=3306
   # DB_USER=fitness_coach_user
   # DB_PASSWORD=FitnessCoach2024!
   # DB_NAME=fitness_coach_db
   
   # Use SQLite instead
   DATABASE_URL=sqlite:///./fitness_coach.db
   ```

2. **Update `app/core/config.py`:**
   ```python
   @property
   def database_url(self) -> str:
       if hasattr(self, '_database_url'):
           return self._database_url
       return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
   ```

## Current Status

✅ **Completed:**
- Python environment setup
- Dependencies installed
- Project structure created
- Configuration files ready
- Database models defined
- API endpoints implemented

⏳ **Pending:**
- Database initialization
- Alembic setup
- Sample data creation
- API testing

## Files Created

- `setup_database.sql` - SQL script for manual database setup
- `test_db_setup.py` - Test database connection and create tables
- `.env` - Environment configuration (database credentials)

## Need Help?

If you're having trouble with MySQL setup:
1. Check if MySQL service is running
2. Verify MySQL root password
3. Consider using MySQL Workbench for easier setup
4. As a last resort, use SQLite for development
