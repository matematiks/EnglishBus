
import sqlite3
import os

db_path = "englishbus.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check UserProgress
    cursor.execute("SELECT COUNT(*) FROM UserProgress")
    up_count = cursor.fetchone()[0]
    print(f"UserProgress Rows: {up_count}")
    
    # Check UserWordProgress
    cursor.execute("SELECT COUNT(*) FROM UserWordProgress")
    uwp_count = cursor.fetchone()[0]
    print(f"UserWordProgress Rows: {uwp_count}")
    
    conn.close()
else:
    print("DB not found")
