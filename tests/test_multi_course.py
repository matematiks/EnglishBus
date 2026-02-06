#!/usr/bin/env python3
"""
Multi-Course Isolation Test
Verifies that same user can progress independently in multiple courses
"""

import sqlite3
import sys

DB_PATH = "englishbus.db"
USER_ID = 1

def reset_user():
    """Clean slate"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM UserProgress WHERE user_id = ?", (USER_ID,))
    conn.execute("DELETE FROM UserCourseProgress WHERE user_id = ?", (USER_ID,))
    conn.commit()
    conn.close()

def get_progress(course_id):
    """Get user progress for course"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT current_step, max_open_unit_order 
        FROM UserCourseProgress
        WHERE user_id = ? AND course_id = ?
    """, (USER_ID, course_id))
    row = cursor.fetchone()
    conn.close()
    return row if row else (None, None)

def initialize_course(course_id):
    """Initialize progress for course"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR IGNORE INTO UserCourseProgress 
        (user_id, course_id, current_step, max_open_unit_order)
        VALUES (?, ?, 1, 1)
    """, (USER_ID, course_id))
    conn.commit()
    conn.close()

def advance_step(course_id, new_step):
    """Manually advance step for testing"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        UPDATE UserCourseProgress 
        SET current_step = ?
        WHERE user_id = ? AND course_id = ?
    """, (new_step, USER_ID, course_id))
    conn.commit()
    conn.close()

print("=" * 60)
print("MULTI-COURSE ISOLATION TEST")
print("=" * 60)
print()

# Test 1: Reset and verify clean state
print("✅ Test 1: Clean State")
print("-" * 60)
reset_user()
step_a1, max_a1 = get_progress(1)
step_a2, max_a2 = get_progress(2)
assert step_a1 is None, "A1 should not exist"
assert step_a2 is None, "A2 should not exist"
print("✅ PASSED - No progress exists")
print()

# Test 2: Initialize A1
print("✅ Test 2: Initialize A1")
print("-" * 60)
initialize_course(1)
step_a1, max_a1 = get_progress(1)
step_a2, max_a2 = get_progress(2)
assert step_a1 == 1 and max_a1 == 1, f"A1 should be (1,1), got ({step_a1},{max_a1})"
assert step_a2 is None, "A2 should still not exist"
print(f"A1: step={step_a1}, max_open={max_a1}")
print("✅ PASSED - A1 initialized, A2 untouched")
print()

# Test 3: Advance A1, verify A2 still empty
print("✅ Test 3: Advance A1 → Step 10")
print("-" * 60)
advance_step(1, 10)
step_a1, max_a1 = get_progress(1)
step_a2, max_a2 = get_progress(2)
assert step_a1 == 10, f"A1 should be step 10, got {step_a1}"
assert step_a2 is None, "A2 should still not exist"
print(f"A1: step={step_a1}, max_open={max_a1}")
print(f"A2: None (not initialized)")
print("✅ PASSED - A1 advanced independently")
print()

# Test 4: Initialize A2, verify A1 unchanged
print("✅ Test 4: Initialize A2, verify A1 unchanged")
print("-" * 60)
initialize_course(2)
step_a1, max_a1 = get_progress(1)
step_a2, max_a2 = get_progress(2)
assert step_a1 == 10, f"A1 should still be 10, got {step_a1}"
assert step_a2 == 1 and max_a2 == 1, f"A2 should be (1,1), got ({step_a2},{max_a2})"
print(f"A1: step={step_a1}, max_open={max_a1}")
print(f"A2: step={step_a2}, max_open={max_a2}")
print("✅ PASSED - Both courses independent")
print()

# Test 5: Advance A2, verify A1 still unchanged
print("✅ Test 5: Advance A2 → Step 5, verify A1 still at 10")
print("-" * 60)
advance_step(2, 5)
step_a1, max_a1 = get_progress(1)
step_a2, max_a2 = get_progress(2)
assert step_a1 == 10, f"A1 should still be 10, got {step_a1}"
assert step_a2 == 5, f"A2 should be 5, got {step_a2}"
print(f"A1: step={step_a1}, max_open={max_a1}")
print(f"A2: step={step_a2}, max_open={max_a2}")
print("✅ PASSED - Complete isolation confirmed")
print()

print("=" * 60)
print("ALL MULTI-COURSE TESTS PASSED ✅")
print("Courses are completely isolated per user")
print("=" * 60)
