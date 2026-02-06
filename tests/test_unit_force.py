import sqlite3
import sys
import os

# Mock the environment to import session_manager
sys.path.insert(0, os.path.abspath("backend"))
from session_manager import get_session_content

DB_PATH = "englishbus.db"

def test_unit_forcing():
    print("🚀 Testing Unit Forcing...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. Simulate User Requesting Unit 2 (Start Study -> Unit 2)
    # Assume Unit 1 is incomplete (words_seen < total).
    # But user explicitely asks for Unit 2.
    
    # Let's assume Unit 2 ID is 2.
    USER_ID = 1 # Demo user
    COURSE_ID = 1
    UNIT_ID = 2
    
    print(f"Requesting content for Unit {UNIT_ID}...")
    result = get_session_content(
        user_id=USER_ID,
        course_id=COURSE_ID,
        db=conn,
        skip_count=0,
        unit_id=UNIT_ID
    )
    
    print(f"Active Unit Returned: {result.get('active_unit_id')}")
    print(f"Current Step: {result.get('current_step')}")
    
    items = result.get('items', [])
    print(f"Items returned: {len(items)}")
    
    for item in items:
        valid = item.get('unit_id') == UNIT_ID
        print(f" - Item: {item.get('english')} (Unit: {item.get('unit_id')}) -> {'✅ OK' if valid else '❌ WRONG UNIT'}")
        
    conn.close()

if __name__ == "__main__":
    try:
        test_unit_forcing()
    except Exception as e:
        print(f"Test failed: {e}")
