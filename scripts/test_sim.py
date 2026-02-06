import sys
import os
import sqlite3
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.session_manager import get_session_content, complete_session
# from backend.database import get_db

DB_PATH = "sim_test.db"

def setup_sim_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Minimal Schema for Test
    conn.execute("CREATE TABLE Users (id INTEGER PRIMARY KEY, username TEXT)")
    conn.execute("CREATE TABLE Courses (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE Units (id INTEGER PRIMARY KEY, course_id INTEGER, order_number INTEGER)")
    conn.execute("CREATE TABLE Words (id INTEGER PRIMARY KEY, course_id INTEGER, unit_id INTEGER, order_number INTEGER, english TEXT, turkish TEXT, image_url TEXT, audio_en_url TEXT, audio_tr_url TEXT)")
    conn.execute("CREATE TABLE UserCourseProgress (user_id INTEGER, course_id INTEGER, current_step INTEGER, max_open_unit_order INTEGER, last_activity TIMESTAMP)")
    conn.execute("CREATE TABLE UserProgress (user_id INTEGER, word_id INTEGER, repetition_count INTEGER, next_review_step INTEGER, last_updated TIMESTAMP, first_learned_at DATE)")
    
    # Seeding
    conn.execute("INSERT INTO Users (id, username) VALUES (1, 'tester')")
    conn.execute("INSERT INTO Courses (id, name) VALUES (1, 'English')")
    conn.execute("INSERT INTO Units (id, course_id, order_number) VALUES (1, 1, 1)")
    
    # Insert 50 Words
    for i in range(1, 51):
        conn.execute(f"INSERT INTO Words (id, course_id, unit_id, order_number, english) VALUES ({i}, 1, 1, {i}, 'Word_{i}')")
        
    conn.commit()
    conn.close()
    print("✅ Test DB Created")

def run_simulation(steps=30):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    user_id = 1
    course_id = 1
    
    print("\n🚀 STARTING SIMULATION (30 Steps)")
    print(f"{'STEP':<6} | {'TYPE':<8} | {'WORD':<10} | {'REP':<4} | {'LOGIC CHECK'}")
    print("-" * 60)
    
    for i in range(steps):
        # 1. Get Content
        # We need check DB for current step first
        cur = conn.execute("SELECT current_step FROM UserCourseProgress WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        real_step = row[0] if row else 1
        
        # Call backend logic
        content = get_session_content(user_id, course_id, conn)
        items = content.get('items', [])
        
        step_log = []
        completed_ids = []
        
        # Analyze Items
        if not items:
            print(f"{real_step:<6} | {'EMPTY':<8} | {'-':<10} | {'-':<4} | (Auto-Skipped)")
        else:
            for item in items:
                w_id = item['word_id']
                w_type = item['type'] # NEW or REVIEW
                w_eng = item['english']
                # w_rep = item.get('repetition_count', 0) # API returns this? check session_manager
                # session_manager.py returns 'repetition_count' in item dict.
                w_rep = item.get('repetition_count', 0)
                
                check_msg = ""
                # Logic Validations
                if w_type == "NEW":
                    if (real_step - 1) % 3 == 0:
                        check_msg = "✅ Valid (1-4-7 rule)"
                    else:
                        check_msg = "❌ INVALID! New word on wrong step!"
                elif w_type == "REVIEW":
                    # Check if it was scheduled for this step
                    # Requires looking up UserProgress before update
                    pass 
                    
                print(f"{real_step:<6} | {w_type:<8} | {w_eng:<10} | {w_rep:<4} | {check_msg}")
                completed_ids.append(w_id)
        
        # 2. Complete Session
        if completed_ids:
            # Re-open conn for transaction safety in simulation? 
            # complete_session creates its own connection... we should close ours or pass one?
            # session_manager.complete_session takes db_path and creates NEW connection.
            # So we close our read connection or just let it be. SQLite handles concurrent reads.
            res = complete_session(user_id, course_id, completed_ids, DB_PATH)
            if res['status'] == 'error':
                print(f"❌ Session Error: {res['error']}")
                break
        else:
            # If empty, get_session_content already incremented step!
            # We just loop again.
            pass

    conn.close()
    
    # Final Stats
    conn = sqlite3.connect(DB_PATH)
    c = conn.execute("SELECT COUNT(*) FROM UserProgress")
    learned = c.fetchone()[0]
    print("\n📊 Final Report:")
    print(f"Total Words Learned: {learned}")
    
    # Verify Fibonacci spacing
    # Pick a random word and trace it?
    cur = conn.execute("SELECT word_id, repetition_count, next_review_step FROM UserProgress WHERE repetition_count > 2 LIMIT 5")
    print("\nFibonacci Check (Sample Words):")
    for r in cur.fetchall():
        print(f"Word {r[0]}: Rep={r[1]}, Next Step={r[2]}")
        
    conn.close()

if __name__ == "__main__":
    setup_sim_db()
    run_simulation()
    # cleanup
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
