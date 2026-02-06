
import sqlite3
import os

# Database Path
# Script is in backend/migrations/ (Depth 2 from backend, Depth 3 from root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "englishbus.db")

def migrate():
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Check if column exists
        cursor = conn.execute("PRAGMA table_info(UserProgress)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "first_learned_at" not in columns:
            print("Adding 'first_learned_at' column to UserProgress...")
            conn.execute("ALTER TABLE UserProgress ADD COLUMN first_learned_at TEXT DEFAULT NULL")
            
            # Backfill: Set first_learned_at = last_updated for existing records
            print("Backfilling data based on last_updated...")
            conn.execute("UPDATE UserProgress SET first_learned_at = date(last_updated) WHERE first_learned_at IS NULL AND last_updated IS NOT NULL")
            
            # For records without last_updated (legacy), set to today or leave null?
            # Let's set to date('now') for safety if they exist, or leave null.
            # Best effort: use last_updated.
            
            conn.commit()
            print("Migration successful: first_learned_at added.")
        else:
            print("Column 'first_learned_at' already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
