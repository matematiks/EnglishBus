import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "englishbus.db")

def check_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get course ID for A1_Foundation
    cursor.execute("SELECT id FROM Courses WHERE name = 'A1_Foundation'")
    res = cursor.fetchone()
    if not res:
        print("Course not found in DB")
        return
    cid = res[0]
    
    # Check apple
    cursor.execute("SELECT english, image_url FROM Words WHERE course_id = ? AND english = 'apple'", (cid,))
    apple = cursor.fetchone()
    print(f"Apple: {apple}")
    
    conn.close()

if __name__ == "__main__":
    check_db()
