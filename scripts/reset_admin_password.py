
import sqlite3
import sys
import bcrypt
import os

# Adjust path to find database in root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "englishbus.db")

def get_password_hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def reset_password(new_password="123456"):
    print(f"Connecting to database at: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("Error: Database file not found!")
        sys.exit(1)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute('SELECT id, username FROM Users WHERE username = ?', ('admin',))
        user = cursor.fetchone()
        
        hashed = get_password_hash(new_password)
        
        if user:
            print(f'Updating password for user {user[1]} (ID: {user[0]})')
            cursor.execute('UPDATE Users SET password_hash = ? WHERE id = ?', (hashed, user[0]))
        else:
            print('Admin user not found. Creating new admin user.')
            cursor.execute('''
                INSERT INTO Users (username, password_hash, is_admin, account_type, approval_status) 
                VALUES (?, ?, 1, 'admin', 'approved')
            ''', ('admin', hashed))
            
        conn.commit()
        print(f'✅ Password reset successfully to: {new_password}')
        conn.close()
    except Exception as e:
        print(f'❌ Error: {e}')
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        reset_password(sys.argv[1])
    else:
        reset_password()
