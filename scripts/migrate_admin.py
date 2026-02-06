import sqlite3
import sys
import os

# Connect to database
DB_PATH = "englishbus.db"

def migrate():
    print(f"Migrating {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if column exists
    try:
        cursor.execute("SELECT is_admin FROM Users LIMIT 1")
        print("Column 'is_admin' already exists.")
    except sqlite3.OperationalError:
        print("Adding 'is_admin' column...")
        try:
            cursor.execute("ALTER TABLE Users ADD COLUMN is_admin INTEGER DEFAULT 0")
            conn.commit()
            print("Successfully added 'is_admin' column.")
            
            # Make the first user admin if exists, or just log
            cursor.execute("SELECT id, username FROM Users LIMIT 1")
            first_user = cursor.fetchone()
            if first_user:
                print(f"Promoting first user ({first_user[1]}) to admin for bootstrap...")
                cursor.execute("UPDATE Users SET is_admin = 1 WHERE id = ?", (first_user[0],))
                conn.commit()
            else:
                print("No users found to promote.")
                
        except Exception as e:
            print(f"Error adding column: {e}")
            conn.rollback()
    
    conn.close()

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
    else:
        migrate()
