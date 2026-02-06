import sqlite3
import sys
import os

# Mock import
sys.path.insert(0, os.path.abspath("backend"))
from session_manager import get_session_content

DB_PATH = "englishbus.db"

def test_leakage():
    print("🛡️ Testing for Unit Leakage...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    USER_ID = 1
    COURSE_ID = 1
    TARGET_UNIT = 1
    
    # Run multiple checks
    for i in range(5):
        print(f"\nCheck {i+1}: Requesting Unit {TARGET_UNIT}...")
        
        # Force different steps to test NEW and REVIEW logic
        # Mocking user progress step?
        # Actually session_manager reads from DB.
        # We can just run it against current state.
        
        result = get_session_content(
            user_id=USER_ID,
            course_id=COURSE_ID,
            db=conn,
            skip_count=0,
            unit_id=TARGET_UNIT
        )
        
        items = result.get('items', [])
        print(f"  -> Received {len(items)} items.")
        
        leak_found = False
        for item in items:
            u_id = item.get('unit_id')
            if u_id != TARGET_UNIT:
                print(f"  🚨 LEAK DETECTED! Item '{item.get('english')}' belongs to Unit {u_id}!")
                leak_found = True
            
        if not leak_found:
            print("  ✅ Clean. All items belong to Unit 1.")
            
        if result.get('active_unit_id') != TARGET_UNIT:
             print(f"  ⚠️ Active Unit ID Mismatch: Expected {TARGET_UNIT}, got {result.get('active_unit_id')}")

    conn.close()

if __name__ == "__main__":
    test_leakage()
