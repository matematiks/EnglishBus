import sqlite3
import os

DB_PATH = 'englishbus.db'

def migrate():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    print("Checking UserProgress schema...")
    cur.execute("PRAGMA table_info(UserProgress)")
    columns = [info[1] for info in cur.fetchall()]
    
    if 'last_updated' in columns:
        print("Column 'last_updated' already exists. Skipping.")
    else:
        print("Adding 'last_updated' column...")
        try:
            # Using NULL default safely
            cur.execute("ALTER TABLE UserProgress ADD COLUMN last_updated TEXT DEFAULT NULL")
            con.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")
    
    con.close()

if __name__ == "__main__":
    migrate()
