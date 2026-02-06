"""
Unit Lock Management - User-Scoped Progressive Unlock
Uses max_open_unit_order in UserCourseProgress for efficient unit access control.
"""

import sqlite3
from typing import Dict, Optional


def get_max_open_unit_order(conn: sqlite3.Connection, user_id: int, course_id: int) -> int:
    """
    Get the highest unit order this user can access.
    
    Returns:
        int: Max open unit order number (default: 1)
    """
    cursor = conn.execute("""
        SELECT max_open_unit_order
        FROM UserCourseProgress
        WHERE user_id = ? AND course_id = ?
    """, (user_id, course_id))
    
    row = cursor.fetchone()
    return row[0] if row else 1


def calc_unit_progress(conn: sqlite3.Connection, user_id: int, unit_id: int) -> Dict[str, float]:
    """
    Calculate progress for a specific unit with TWO-TIER metrics.
    
    HYBRID APPROACH (Production Decision 2025-12-15):
    - "Seen" = repetition_count >= 1 (introduced to user)
    - "Mastered" = repetition_count >= 3 (reinforced 4 times: steps +1,+1,+2)
    
    This balances MVP speed with pedagogical soundness.
    
    EDGE CASE: Empty units (total=0) are considered 100% to avoid deadlock
    
    Returns:
        {
            "total": int,           # Total words in unit
            "seen": int,            # Words with rep_count >= 1  
            "mastered": int,        # Words with rep_count >= 3
            "seen_percentage": float,      # (seen / total) * 100
            "mastered_percentage": float   # (mastered / total) * 100
        }
    """
    # Get total, seen, and mastered in single query
    cursor = conn.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN COALESCE(up.repetition_count, 0) >= 1 THEN 1 ELSE 0 END) AS seen,
            SUM(CASE WHEN COALESCE(up.repetition_count, 0) >= 3 THEN 1 ELSE 0 END) AS mastered
        FROM Words w
        LEFT JOIN UserProgress up 
            ON up.word_id = w.id AND up.user_id = ?
        WHERE w.unit_id = ?
    """, (user_id, unit_id))
    
    row = cursor.fetchone()
    total = row[0] if row else 0
    seen = row[1] if row and row[1] else 0
    mastered = row[2] if row and row[2] else 0
    
    # EDGE CASE: Empty unit (total=0) → 100% to avoid blocking progression
    if total == 0:
        return {
            "total": 0,
            "seen": 0,
            "mastered": 0,
            "seen_percentage": 100.0,
            "mastered_percentage": 100.0
        }
    
    seen_pct = (seen / total * 100.0)
    mastered_pct = (mastered / total * 100.0)
    
    return {
        "total": total,
        "seen": seen,
        "mastered": mastered,
        "seen_percentage": seen_pct,
        "mastered_percentage": mastered_pct
    }


def try_unlock_next_unit(conn: sqlite3.Connection, user_id: int, course_id: int):
    """
    Check if next unit should unlock based on current progress.
    Updates max_open_unit_order if threshold met.
    
    CRITICAL: Called inside transaction (does NOT commit)
    
    Unlock Rules:
    - Unit 2: Unit 1 >= 50%
    - Unit k+2 (k>=1): Unit k >= 100% AND Unit k+1 >= 50%
    
    This prevents skipping: A1.3 cannot unlock until A1.1 is 100% complete
    
    Args:
        conn: Database connection (in transaction)
        user_id: User ID
        course_id: Course ID
    """
    # Get current max_open
    max_open = get_max_open_unit_order(conn, user_id, course_id)
    
    # Find current unit (at max_open order)
    cursor = conn.execute("""
        SELECT id
        FROM Units
        WHERE course_id = ? AND order_number = ?
    """, (course_id, max_open))
    
    current_unit = cursor.fetchone()
    if not current_unit:
        return  # No unit at this order (shouldn't happen)
    
    current_unit_id = current_unit[0]
    
    # Check if next unit exists
    cursor = conn.execute("""
        SELECT id
        FROM Units
        WHERE course_id = ? AND order_number = ?
    """, (course_id, max_open + 1))
    
    next_unit = cursor.fetchone()
    if not next_unit:
        return  # No more units to unlock
    
    # Calculate current unit progress
    current_progress = calc_unit_progress(conn, user_id, current_unit_id)
    
    # TWO-UNIT PREVENTION LOGIC with HYBRID METRICS
    # Unit 2: "seen" 50% (rep>=1)
    # Unit k+2: "mastered" 100% (rep>=3) + "seen" 50%
    can_unlock = False
    
    if max_open == 1:
        # Unlocking Unit 2: only need Unit 1 >= 50% SEEN
        can_unlock = current_progress["seen_percentage"] >= 50.0
    else:
        # Unlocking Unit k+2: need Unit k >= 100% MASTERED AND Unit k+1 >= 50% SEEN
        # Get previous unit (k = max_open - 1)
        cursor = conn.execute("""
            SELECT id
            FROM Units
            WHERE course_id = ? AND order_number = ?
        """, (course_id, max_open - 1))
        
        prev_unit = cursor.fetchone()
        if prev_unit:
            prev_unit_id = prev_unit[0]
            prev_progress = calc_unit_progress(conn, user_id, prev_unit_id)
            
            # Both conditions must be met (MASTERED vs SEEN)
            can_unlock = (
                prev_progress["mastered_percentage"] >= 100.0 and
                current_progress["seen_percentage"] >= 50.0
            )
    
    if can_unlock:
        conn.execute("""
            UPDATE UserCourseProgress
            SET max_open_unit_order = ?
            WHERE user_id = ? AND course_id = ?
        """, (max_open + 1, user_id, course_id))
        
        print(f"🔓 Unit unlocked: {course_id} unit order {max_open + 1} for user {user_id}")


def get_all_units_status(conn: sqlite3.Connection, user_id: int, course_id: int) -> list:
    """
    Get status and progress for all units in a course.
    
    Returns:
        List of dicts: [{unit_id, name, order, status, progress}, ...]
    """
    max_open = get_max_open_unit_order(conn, user_id, course_id)
    
    cursor = conn.execute("""
        SELECT id, name, order_number
        FROM Units
        WHERE course_id = ?
        ORDER BY order_number
    """, (course_id,))
    
    units = []
    for unit_id, name, order_num in cursor.fetchall():
        status = "OPEN" if order_num <= max_open else "LOCKED"
        progress = calc_unit_progress(conn, user_id, unit_id)
        
        units.append({
            "unit_id": unit_id,
            "name": name,
            "order": order_num,
            "status": status,
            "progress": progress
        })
    
    return units
