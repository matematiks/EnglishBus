"""
Session Manager - Core Learning Algorithm
Implements Fibonacci-based spaced repetition with step-based tracking
"""

import sqlite3
from typing import List, Dict, Any, Tuple, Optional


def fibonacci(n: int) -> int:
    """
    Calculate nth Fibonacci number using iterative approach for efficiency.
    CANONICAL SEQUENCE (1-indexed):
    
        fibonacci(1) = 1
        fibonacci(2) = 1
        fibonacci(3) = 2
        fibonacci(5) = 5
        fibonacci(10) = 55
    
    Args:
        n: Position in Fibonacci sequence (1-indexed)
    
    Returns:
        nth Fibonacci number
    """
    if n <= 0:
        return 0
    if n <= 2:
        return 1
    
    a, b = 1, 1
    for _ in range(n - 2):
        a, b = b, a + b
    return b


def get_user_step(conn: sqlite3.Connection, user_id: int, course_id: int) -> int:
    """
    Get current step for user in specified course.
    Creates initial progress record if doesn't exist.
    
    CRITICAL: This is PER-COURSE tracking. Each course has independent step.
    
    Args:
        conn: Database connection (in transaction)
        user_id: User ID
        course_id: Course ID
    
    Returns:
        Current step number
    """
    # 1. Get User Progress
    row = conn.execute("""
        SELECT current_step, max_open_unit_order 
        FROM UserCourseProgress 
        WHERE user_id = ? AND course_id = ?
    """, (user_id, course_id)).fetchone()
    
    if not row:
        # Auto-initialize progress for this course if missing
        conn.execute("""
            INSERT INTO UserCourseProgress (user_id, course_id, current_step, max_open_unit_order)
            VALUES (?, ?, 1, 1)
        """, (user_id, course_id))
        conn.commit() # Commit the insert immediately
        current_step = 1
        max_open_unit = 1 # This variable is not returned, but is part of the new logic
    else:
        current_step = row[0]
        max_open_unit = row[1] # This variable is not returned, but is part of the new logic
    
    return current_step


def update_word_progress(conn: sqlite3.Connection, user_id: int, word_id: int, current_step: int):
    """
    Update a word's repetition count and calculate next review step.
    Uses PURE Fibonacci sequence for spacing: 1,1,2,3,5,8,13,21,34...
    
    IDEMPOTENCY: Ignores re-submission of same word in same step.
    
    Args:
        conn: Database connection (in transaction)
        user_id: User ID
        word_id: Word ID
        current_step: Current step number (from UserCourseProgress)
    """
    # IDEMPOTENCY CHECK: If word already processed for future step, skip
    cursor = conn.execute("""
        SELECT repetition_count, next_review_step 
        FROM UserProgress 
        WHERE user_id = ? AND word_id = ?
    """, (user_id, word_id))
    
    row = cursor.fetchone()
    
    if row:
        old_rep_count, old_next_review = row
        
        # IDEMPOTENCY: If this word was already scheduled BEYOND current step, ignore
        if old_next_review > current_step:
            print(f"⚠️ Duplicate submission: Word {word_id} already scheduled for step {old_next_review}")
            return
        
        # Increment repetition count
        new_rep_count = old_rep_count + 1
        fib_gap = fibonacci(new_rep_count)
        next_review = current_step + fib_gap
        
        conn.execute("""
            UPDATE UserProgress 
            SET repetition_count = ?, next_review_step = ?, last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ? AND word_id = ?
        """, (new_rep_count, next_review, user_id, word_id))
        
        print(f"✓ Word {word_id}: rep {old_rep_count}→{new_rep_count}, next step {old_next_review}→{next_review} (gap: {fib_gap})")
    else:
        # First encounter: Initialize with rep_count=1
        # Next review uses Fibonacci[1] = +1 step
        next_review = current_step + 1
        
        conn.execute("""
            INSERT INTO UserProgress (user_id, word_id, repetition_count, next_review_step, last_updated, first_learned_at)
            VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP, date('now'))
        """, (user_id, word_id, next_review))


def get_session_content(
    user_id: int, 
    course_id: int, 
    db: sqlite3.Connection, 
    skip_count: int = 0,
    unit_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get cards for current step using 1-4-7-10 rule and Fibonacci reviews.
    
    CORE ALGORITHM:
    - New word on steps: 1, 4, 7, 10, 13... (when (step-1) % 3 == 0)
    - Review words: where next_review_step == current_step
    - Empty steps: Auto-increment and recurse
    
    Args:
        user_id: User ID
        course_id: Course ID
        db: Database connection
        skip_count: Recursion depth (avalanche guard)
        unit_id: Optional unit ID to filter content
    
    Returns:
        {
            'current_step': int,
            'items': List[{...card data...}],
            'message': str (optional, if no cards found)
        }
    """
    try:
        current_step = get_user_step(db, user_id, course_id)
    except Exception as e:
        print(f"❌ Error getting user step: {e}")
        current_step = 1
    
    study_list = []
    unit_filter_msg = f", Unit {unit_id}" if unit_id else ""
    print(f"📚 User {user_id}, Course {course_id}, Step {current_step}, Skip {skip_count}{unit_filter_msg}")
    
    # RULE 1: New Word Check (1-4-7-10 pattern)
    is_new_word_step = (current_step - 1) % 3 == 0
    # Override: If user manually selected a unit, we ALWAYS try to give them a new word from that unit
    # regardless of the "step" rule, otherwise they might get an empty session if they are on a review step.
    if unit_id:
        is_new_word_step = True
    
    if is_new_word_step:
        # Get next unseen word
        # LOGIC BRANCH: 
        # If unit_id is specified -> Fetch next new word from THAT unit (Ignore step/lock limits)
        # If unit_id is None -> Fetch next new word from OPEN units (Respect step/lock limits)

        if unit_id:
            # --- MANUAL UNIT SELECTION MODE ---
            query = """
                SELECT W.id, W.english, W.turkish, W.image_url, W.audio_en_url, W.audio_tr_url, W.order_number, W.unit_id
                FROM Words W
                WHERE W.course_id = ?
                AND W.unit_id = ?
                AND W.id NOT IN (
                    SELECT word_id FROM UserProgress WHERE user_id = ?
                )
                ORDER BY W.order_number
                LIMIT 1
            """
            params = (course_id, unit_id, user_id)
        else:
            # --- CONTINUOUS CURRICULUM MODE ---
            # Get max_open_unit_order for this user
            cursor = db.execute("""
                SELECT max_open_unit_order
                FROM UserCourseProgress
                WHERE user_id = ? AND course_id = ?
            """, (user_id, course_id))
            
            row = cursor.fetchone()
            max_open = row[0] if row else 1
            
            query = """
                SELECT W.id, W.english, W.turkish, W.image_url, W.audio_en_url, W.audio_tr_url, W.order_number, W.unit_id
                FROM Words W
                JOIN Units u ON W.unit_id = u.id
                WHERE W.course_id = ?
                  AND W.order_number <= ?
                  AND u.order_number <= ?
                  AND W.id NOT IN (
                      SELECT word_id FROM UserProgress WHERE user_id = ?
                  )
                ORDER BY W.order_number
                LIMIT 1
            """
            params = (course_id, current_step, max_open, user_id)
        
        cursor = db.execute(query, params)
        new_word = cursor.fetchone()
        
        if new_word:
            study_list.append({
                "type": "NEW",
                "word_id": new_word['id'],
                "english": new_word['english'],
                "turkish": new_word['turkish'],
                "image_url": new_word['image_url'],
                "audio_en_url": new_word['audio_en_url'],
                "audio_tr_url": new_word['audio_tr_url'],
                "order_number": new_word['order_number'],
                "repetition_count": 0,
                "unit_id": new_word['unit_id'],
                "logical_address": f"{user_id}.{course_id}.{new_word['unit_id']}.{new_word['order_number']}"
            })
            # CAPTURE THE UNIT ID OF THE NEW WORD
            if unit_id is None:
                unit_id = new_word['unit_id']

            print(f"  ✨ NEW word: {new_word['english']} (Unit {unit_id})")
        else:
            print(f"  ℹ️ No more new words available")
    
    # RULE 2: Review Words (Fibonacci-scheduled)
    # Modified to include Unid ID filter
    base_review_query = """
        SELECT P.word_id, P.repetition_count, 
               W.english, W.turkish, W.image_url, W.audio_en_url, W.audio_tr_url, W.order_number, W.unit_id
        FROM UserProgress P
        JOIN Words W ON P.word_id = W.id
        WHERE P.user_id = ?
        AND P.next_review_step = ?
        AND W.course_id = ?
    """
    review_params = [user_id, current_step, course_id]
    
    if unit_id:
        base_review_query += " AND W.unit_id = ?"
        review_params.append(unit_id)
        
    cursor = db.execute(base_review_query, review_params)
    
    reviews = cursor.fetchall()
    
    for row in reviews:
        study_list.append({
            "type": "REVIEW",
            "word_id": row['word_id'],
            "english": row['english'],
            "turkish": row['turkish'],
            "image_url": row['image_url'],
            "audio_en_url": row['audio_en_url'],
            "audio_tr_url": row['audio_tr_url'],
            "order_number": row['order_number'],
            "order_number": row['order_number'],
            "repetition_count": row['repetition_count'],
            "unit_id": row['unit_id'],
            "logical_address": f"{user_id}.{course_id}.{row['unit_id']}.{row['order_number']}"
        })
        
        # Fallback: If we assume "Active Unit" is the unit of the words we are studying...
        if unit_id is None:
            unit_id = row['unit_id']
            
        print(f"  🔄 REVIEW word: {row['english']} (rep: {row['repetition_count']})")
    
    # RULE 3: Empty Step Handling
    if study_list:
        return {
            "current_step": current_step,
            "items": study_list,
            "active_unit_id": unit_id
        }
    else:
        # Recursion guard
        if skip_count > 200:
            print(f"⚠️ Recursion limit reached at step {current_step}")
            return {
                "current_step": current_step,
                "items": [],
                "message": "No cards found after 200 steps",
                "active_unit_id": unit_id
            }
        
        print(f"  ⏭️ Step {current_step} is empty, incrementing...")
        
        # Increment step and try again
        db.execute("""
            UPDATE UserCourseProgress
            SET current_step = current_step + 1,
            last_activity = CURRENT_TIMESTAMP
            WHERE user_id = ? AND course_id = ?
        """, (user_id, course_id))
        db.commit()
        
        # Pass unit_id to recursion
        return get_session_content(user_id, course_id, db, skip_count + 1, unit_id=unit_id)


def complete_session(user_id: int, course_id: int, completed_word_ids: List[int], db_path: str = 'englishbus.db') -> Dict[str, Any]:
    """
    Atomically update user progress after completing a study session.
    
    CRITICAL: This function ensures all-or-nothing consistency.
    Either ALL updates succeed, or NONE persist (rollback on error).
    
    Args:
        user_id: User ID
        course_id: Course ID
        completed_word_ids: List of word IDs completed in this session
        db_path: Path to SQLite database
    
    Returns:
        {
            'status': 'success' | 'error',
            'new_step': int (if success),
            'words_updated': int (if success),
            'error': str (if error)
        }
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # Start transaction
        current_step = get_user_step(conn, user_id, course_id)
        
        # Update each word
        for word_id in completed_word_ids:
            update_word_progress(conn, user_id, word_id, current_step)
        
        # Increment user's current step
        conn.execute("""
            UPDATE UserCourseProgress 
            SET current_step = current_step + 1,
                last_activity = CURRENT_TIMESTAMP
            WHERE user_id = ? AND course_id = ?
        """, (user_id, course_id))
        
        new_step = current_step + 1
        
        # Calculate Daily New Words (Cumulative for today using Creation Date)
        cursor = conn.execute("""
            SELECT COUNT(*) 
            FROM UserProgress 
            WHERE user_id = ? 
            AND date(first_learned_at) = date('now')
        """, (user_id,))
        daily_count = cursor.fetchone()[0]
        
        # Commit transaction
        conn.commit()
        
        return {
            'status': 'success',
            'new_step': new_step,
            'words_updated': len(completed_word_ids),
            'daily_new_count': daily_count
        }
    
    except Exception as e:
        # Rollback on error
        conn.rollback()
        return {
            'status': 'error',
            'error': str(e)
        }
    
    finally:
        conn.close()


# ==========================================
# DIAGNOSTIC / DEBUG FUNCTIONS
# ==========================================

def print_fibonacci_table(max_n: int = 20):
    """Print Fibonacci sequence for verification"""
    print("\nFibonacci Sequence:")
    print("=" * 30)
    for i in range(1, max_n + 1):
        print(f"Fibonacci[{i}] = {fibonacci(i)}")
    print("=" * 30)


if __name__ == "__main__":
    # Run diagnostic
    print_fibonacci_table(15)
