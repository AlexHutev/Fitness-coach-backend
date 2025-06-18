from sqlalchemy import create_engine, text
from app.core.config import settings

# Create engine
engine = create_engine(settings.database_url_computed)

# Add the user_id column to clients table
with engine.connect() as conn:
    try:
        # Check if column exists first
        result = conn.execute(text('PRAGMA table_info(clients)'))
        columns = [row[1] for row in result.fetchall()]
        
        if 'user_id' not in columns:
            conn.execute(text('ALTER TABLE clients ADD COLUMN user_id INTEGER'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS ix_clients_user_id ON clients(user_id)'))
            conn.commit()
            print('Added user_id column to clients table')
        else:
            print('user_id column already exists')
            
        # Check if CLIENT role exists
        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role = 'CLIENT'"))
        client_count = result.fetchone()[0]
        print(f'Found {client_count} users with CLIENT role')
        
    except Exception as e:
        print(f'Error: {e}')
        conn.rollback()
