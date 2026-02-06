import sqlite3
import os

DB_PATH = 'englishbus.db'

def fix_counts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Recalculating unit word counts...")
    
    # Update Units.word_count based on count of Words
    cursor.execute("""
        UPDATE Units 
        SET word_count = (
            SELECT COUNT(*) 
            FROM Words 
            WHERE Words.unit_id = Units.id
        )
    """)
    
    conn.commit()
    print("✅ Units table updated.")
    
    # Verify
    rows = cursor.execute("SELECT id, name, word_count FROM Units").fetchall()
    for r in rows:
        print(r)
        
    conn.close()

if __name__ == "__main__":
    fix_counts()
