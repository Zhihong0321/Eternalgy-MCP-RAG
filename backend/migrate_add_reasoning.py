import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Determine DB URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not set. Skipping migration.")
    sys.exit(0)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def run_migration():
    print("Checking for 'reasoning_enabled' column in 'zairag_agents'...")
    try:
        with engine.connect() as connection:
            # Check if column exists (Postgres specific check, or just try catch)
            # Simplest for cross-db is just try to add it and catch error if exists
            try:
                connection.execute(text("ALTER TABLE zairag_agents ADD COLUMN reasoning_enabled BOOLEAN DEFAULT TRUE"))
                connection.commit()
                print("Added column 'reasoning_enabled'.")
            except Exception as e:
                # Likely already exists
                print(f"Column likely exists or error: {e}")
                
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
