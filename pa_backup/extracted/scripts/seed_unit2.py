import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "englishbus.db")

def unlock_unit_2():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if record exists
        cursor.execute("SELECT * FROM UserCourseProgress WHERE user_id = 1 AND course_id = 1")
        record = cursor.fetchone()
        
        if record:
            print("Found existing record. Updating...")
            cursor.execute("""
                UPDATE UserCourseProgress 
                SET max_open_unit_order = 2 
                WHERE user_id = 1 AND course_id = 1
            """)
        else:
            print("No record found. Inserting new record...")
            cursor.execute("""
                INSERT INTO UserCourseProgress (user_id, course_id, current_step, max_open_unit_order) 
                VALUES (1, 1, 1, 2)
            """)
            
        conn.commit()
        print("✅ Unit 2 Unlocked for User 1.")
        
        # Verify
        cursor.execute("SELECT max_open_unit_order FROM UserCourseProgress WHERE user_id = 1")
        val = cursor.fetchone()[0]
        print(f"Current Max Open Unit: {val}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    unlock_unit_2()
