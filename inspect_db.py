
import sqlite3
import os

db_path = "englishbus.db"

print(f"--- INSPECTING {db_path} ---")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:")
    for t in tables:
        print(f" - {t[0]}")
        
    # Check specific columns
    target_tables = ["UserProgress", "UserWordProgress", "UserCourseProgress"]
    for t in target_tables:
        print(f"\nDetails for {t}:")
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{t}';")
        if cursor.fetchone():
            cursor.execute(f"PRAGMA table_info({t})")
            cols = cursor.fetchall()
            print(f"   Columns: {[c[1] for c in cols]}")
            
            # Check for user_id
            if 'user_id' in [c[1] for c in cols]:
                print(f"   [OK] user_id column exists.")
            else:
                print(f"   [CRITICAL] user_id column MISSING!")
        else:
            print("   [MISSING] Table not found.")

    conn.close()
else:
    print(f"Error: {db_path} not found.")
