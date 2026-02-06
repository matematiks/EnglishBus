import sqlite3
import os

DB_PATH = 'englishbus.db'

def unlock_all():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Unlocking all units for all users...")
    
    # Force max_open_unit_order to 15 (covers our 7 units)
    cursor.execute("""
        UPDATE UserCourseProgress 
        SET max_open_unit_order = 15
    """)
    
    conn.commit()
    print("✅ UserCourseProgress updated: All units unlocked.")
        
    conn.close()

if __name__ == "__main__":
    unlock_all()
