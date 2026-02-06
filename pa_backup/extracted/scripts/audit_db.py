import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "englishbus.db")

def audit_words():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        print("📊 Auditing Unit Distributions...")
        
        # Get Units
        units = conn.execute("SELECT id, name, word_count FROM Units ORDER BY id").fetchall()
        
        for u in units:
            print(f"\nUnit {u['id']}: {u['name']} (Target: {u['word_count']})")
            
            # Count actual words
            count = conn.execute("SELECT COUNT(*) FROM Words WHERE unit_id = ?", (u['id'],)).fetchone()[0]
            print(f"  -> Actual Words in DB: {count}")
            
            # Check ID Range
            min_max = conn.execute("SELECT MIN(id), MAX(id), MIN(order_number), MAX(order_number) FROM Words WHERE unit_id = ?", (u['id'],)).fetchone()
            print(f"  -> ID Range: {min_max[0]} - {min_max[1]}")
            print(f"  -> Order Range: {min_max[2]} - {min_max[3]}")
            
            if count != u['word_count']:
                print(f"  ⚠️ MISMATCH: Meta says {u['word_count']}, DB has {count}")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    audit_words()
