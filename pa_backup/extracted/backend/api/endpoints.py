"""
API endpoint handlers
Implements API_CONTRACT.md v1.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3
import sys
import os
import uuid

# Add parent directory to path for session_manager import
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.models import *
from api.dependencies import get_db
from session_manager import complete_session, get_session_content
from api.security_dep import get_current_user
from api.security_utils import verify_password
router = APIRouter()

# Constants
MAX_ITEMS_PER_SESSION = 40  # Avalanche guard


# ============================================
# ENDPOINTS
# ============================================

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "EnglishBus API",
        "version": "1.0.0"
    }


# ============================================
# COURSES & CURRICULUM
# ============================================


@router.get("/courses")
def get_courses(db: sqlite3.Connection = Depends(get_db)):
    """Get all available courses"""
    cursor = db.execute("""
        SELECT id, name, 
               (SELECT COUNT(*) FROM Words WHERE course_id = Courses.id) as total_words
        FROM Courses
        ORDER BY id
    """)
    
    courses = []
    for row in cursor.fetchall():
        courses.append({
            "id": row[0],
            "name": row[1],
            "total_words": row[2]
        })
    
    return {"courses": courses}


@router.post("/reset")
async def reset_progress(
    request: ResetRequest,
    db: sqlite3.Connection = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    """
    Reset user progress for a course with authentication.
    Requires JWT token and password verification.
    Deletes all UserProgress and UserCourseProgress for the user.
    """
    # Verify password
    cursor = db.execute("SELECT password_hash FROM Users WHERE id = ?", (current_user,))
    row = cursor.fetchone()
    if not row or not row[0]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or password not set")
    stored_hash = row[0]
    if not verify_password(request.password, stored_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    try:
        db.execute("DELETE FROM UserProgress WHERE user_id = ?", (current_user,))
        db.execute("DELETE FROM UserCourseProgress WHERE user_id = ? AND course_id = ?", 
                   (current_user, request.course_id))
        # Clear learned words memory for sentence generator
        db.execute("DELETE FROM UserWordProgress WHERE user_id = ?", (current_user,))
        db.commit()
        
        return {
            "status": "success",
            "message": "Progress reset complete",
            "user_id": current_user,
            "course_id": request.course_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.post("/session/start", response_model=SessionStartResponse)
def start_session(
    request: SessionStartRequest,
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Start a new learning session using Fibonacci-based spaced repetition.
    
    Uses get_session_content() which implements:
    - 1-4-7-10 new word rule
    - Fibonacci review scheduling
    - Automatic empty step skipping
    """
    try:
        session_id = uuid.uuid4()
        session_id = uuid.uuid4()
        print(f"🚀 START SESSION REQUEST: User={request.user_id}, Unit={request.unit_id} (Type: {type(request.unit_id)})")
        
        # Call core session manager function
        result = get_session_content(
            user_id=request.user_id,
            course_id=request.course_id,
            db=db,
            skip_count=0,
            unit_id=request.unit_id
        )
        
        # Get unit progress info for the study screen
        unit_progress = None
        if result.get('active_unit_id'):
            unit_id = result['active_unit_id']
            # Count words seen in this unit
            cursor = db.execute("""
                SELECT COUNT(DISTINCT w.id) as total,
                       COUNT(DISTINCT up.word_id) as seen
                FROM Words w
                LEFT JOIN UserProgress up ON w.id = up.word_id AND up.user_id = ?
                WHERE w.unit_id = ?
            """, (request.user_id, unit_id))
            row = cursor.fetchone()
            if row:
                unit_progress = {
                    "total": row[0],
                    "new_words": row[1],  # Frontend expects "new_words" field
                    "seen": row[1]
                }
        
        response_data = {
            "session_id": str(result.get('session_id', session_id)),
            "current_step": result['current_step'],
            "items": result['items'],
            "active_unit_id": result.get('active_unit_id'),
            "total_count": len(result['items']),
            "has_more": False
        }
        
        # Add unit_progress if available
        if unit_progress:
            response_data["unit_progress"] = unit_progress
        
        return SessionStartResponse(**response_data)
        
    except Exception as e:
        print(f"❌ Session start error: {e}")
        raise HTTPException(status_code=500, detail=f"Session start failed: {str(e)}")
    
    # Reached recursion limit
    raise HTTPException(status_code=404, detail="No cards available in this course")


@router.post("/session/complete", response_model=SessionCompleteResponse)
def complete_session_endpoint(
    request: SessionCompleteRequest,
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Complete a session and update progress atomically.
    
    Uses atomic transaction from session_manager.
    """
    db.close()  # Close FastAPI's connection, session_manager will create its own
    
    try:
        # Get correct DB path
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "../englishbus.db")
        db_path = os.path.normpath(db_path)
        
        # Filter out Sentence Mode dummy IDs (strings or 'sent_')
        valid_ids = []
        for wid in request.completed_word_ids:
            if isinstance(wid, int):
                valid_ids.append(wid)
            elif isinstance(wid, str) and wid.isdigit():
                valid_ids.append(int(wid))
        
        # If no valid word IDs (pure sentence practice), just mock success
        if not valid_ids:
            return SessionCompleteResponse(
                status="success",
                new_step=1, # No step change
                words_updated=0,
                daily_new_count=0,
                unit_completed=False,
                course_completed=False
            )

        # Use session_manager's atomic implementation
        result = complete_session(
            user_id=request.user_id,
            course_id=request.course_id,
            completed_word_ids=valid_ids,
            db_path=db_path
        )
        
        
        if result['status'] == 'success':
            # Check if unit/course is completed
            with sqlite3.connect(db_path) as check_db:
                check_db.row_factory = sqlite3.Row
                
                # Count total words in course
                cursor = check_db.execute(
                    "SELECT COUNT(*) as total FROM Words WHERE course_id = ?",
                    (request.course_id,)
                )
                total_words = cursor.fetchone()['total']
                
                # Count completed words for this user in this course
                cursor = check_db.execute(
                    "SELECT COUNT(DISTINCT word_id) as completed FROM UserProgress WHERE user_id = ? AND word_id IN (SELECT id FROM Words WHERE course_id = ?)",
                    (request.user_id, request.course_id)
                )
                completed_words = cursor.fetchone()['completed']
                
                unit_completed = completed_words >= total_words
                course_completed = unit_completed  # For now, course = unit
            
            return SessionCompleteResponse(
                status="success",
                new_step=result['new_step'],
                words_updated=result['words_updated'],
                daily_new_count=result.get('daily_new_count', 0),
                unit_completed=unit_completed,
                course_completed=course_completed
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Unknown error')
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session complete failed: {str(e)}")


@router.get("/courses/{course_id}/progress")
def get_course_progress(
    course_id: int,
    user_id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Get user's progress in a course
    Returns: new_words_seen count and total_words
    """
    try:
        # Count total words in course
        cursor = db.execute(
            "SELECT COUNT(*) as total FROM Words WHERE course_id = ?",
            (course_id,)
        )
        total_words = cursor.fetchone()['total']
        
        # Count NEW words seen (words in UserProgress)
        cursor = db.execute(
            """
            SELECT COUNT(DISTINCT word_id) as seen 
            FROM UserProgress 
            WHERE user_id = ? 
            AND word_id IN (SELECT id FROM Words WHERE course_id = ?)
            """,
            (user_id, course_id)
        )
        new_words_seen = cursor.fetchone()['seen']
        
        return {
            "new_words_seen": new_words_seen,
            "total_words": total_words,
            "progress_percentage": round((new_words_seen / total_words * 100), 1) if total_words > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@router.get("/courses/{course_id}/units")
def get_course_units(
    course_id: int,
    user_id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Get all units in a course with progress for each unit
    Units unlock when previous unit is 80%+ complete
    """
    try:
        # Get all units
        cursor = db.execute(
            """
            SELECT id, name, order_number, word_count 
            FROM Units 
            WHERE course_id = ? 
            ORDER BY order_number
            """,
            (course_id,)
        )
        units = cursor.fetchall()
        
        # Get user's current global step
        cursor = db.execute(
            "SELECT current_step FROM UserCourseProgress WHERE user_id = ? AND course_id = ?",
            (user_id, course_id)
        )
        step_row = cursor.fetchone()
        current_step = step_row['current_step'] if step_row else 1
        
        # Calculate Max Order Number exposed to user
        max_sent_order = ((current_step - 1) // 3) + 1
        
        # Calculate Daily New Words for Dashboard
        cursor = db.execute("""
            SELECT COUNT(*) 
            FROM UserProgress 
            WHERE user_id = ? 
            AND date(first_learned_at) = date('now')
        """, (user_id,))
        daily_new_count = cursor.fetchone()[0]

        result = []
        for unit in units:
            unit_id = unit['id']
            unit_order = unit['order_number']
            total_words = unit['word_count']
            
            # Deterministic Progress Calculation
            cursor = db.execute(
                """
                SELECT COUNT(*) as seen
                FROM Words W
                WHERE W.unit_id = ? 
                AND W.order_number <= ?
                """,
                (unit_id, max_sent_order)
            )
            seen_count = cursor.fetchone()['seen']
            
            progress_pct = round((seen_count / total_words * 100), 1) if total_words > 0 else 0
            
            # FORCE UNLOCK MODE (User Request: "Tüm kilitleri aç")
            # Always OPEN, Always Unlocked
            result.append({
                "unit_id": unit_id,
                "name": unit['name'],
                "order_number": unit_order,
                "total_words": total_words,
                "words_seen": seen_count,
                "progress_percentage": progress_pct,
                "status": "OPEN",
                "is_locked": False
            })
        
        # No need for the "Unlock Next Unit" loop because EVERYTHING IS OPEN.
        
        print(f"🔓 Serving {len(result)} units (ALL FORCED OPEN)")
        return {"units": result, "daily_new_count": daily_new_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get units: {str(e)}")


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_session_items(
    db: sqlite3.Connection,
    user_id: int,
    course_id: int,
    current_step: int
) -> List[WordItem]:
    """
    Get NEW and REVIEW words for current step.
    
    Business Rules per uygulama.text:
    - NEW: Only on steps 1,4,7,10,13,16... [(current_step - 1) % 3 == 0]
           AND order_number <= current_step AND not yet seen
    - REVIEW: next_review_step <= current_step
    
    ORDER: REVIEW words first (warm up memory), then NEW words
    """
    items = []
    
    # RULE B: Review words FIRST (Fibonacci-based)
    # Get words scheduled for review at this step
    # ORDER: Higher order_number first (words learned later = higher priority)
    review_words = db.execute("""
        SELECT w.id, w.english, w.turkish, w.image_url, w.audio_en_url, w.audio_tr_url, w.order_number, up.repetition_count
        FROM Words w
        JOIN UserProgress up ON w.id = up.word_id
        WHERE up.user_id = ?
          AND w.course_id = ?
          AND up.next_review_step <= ?
        ORDER BY w.order_number DESC
    """, (user_id, course_id, current_step)).fetchall()
    
    for word in review_words:
        items.append(WordItem(
            word_id=word[0],
            english=word[1],
            turkish=word[2],
            type="REVIEW",
            image_url=word[3],
            audio_en_url=word[4],
            audio_tr_url=word[5],
            order_number=word[6],
            repetition_count=word[7]
        ))
    
    # RULE A: New Word Introduction SECOND (1-4-7-10 pattern)
    # Formula: (current_step - 1) % 3 == 0
    # Steps: 1, 4, 7, 10, 13, 16, 19...
    # FILTER: Only from OPEN units (order_number <= max_open_unit_order)
    if (current_step - 1) % 3 == 0:
        # Get max_open_unit_order for this user
        cursor = db.execute("""
            SELECT max_open_unit_order
            FROM UserCourseProgress
            WHERE user_id = ? AND course_id = ?
        """, (user_id, course_id))
        
        row = cursor.fetchone()  # CRITICAL: Store result first
        max_open = row[0] if row else 1  # Then use it
        
        new_words = db.execute("""
            SELECT w.id, w.english, w.turkish, w.image_url, w.audio_en_url, w.audio_tr_url, w.order_number
            FROM Words w
            JOIN Units u ON w.unit_id = u.id
            LEFT JOIN UserProgress up ON w.id = up.word_id AND up.user_id = ?
            WHERE w.course_id = ?
              AND w.order_number <= ?
              AND u.order_number <= ?
              AND (up.repetition_count IS NULL OR up.repetition_count = 0)
            ORDER BY w.order_number
            LIMIT 1
        """, (user_id, course_id, current_step, max_open)).fetchall()
        
        for word in new_words:
            items.append(WordItem(
                word_id=word[0],
                english=word[1],
                turkish=word[2],
                type="NEW", # Assuming new words are always type "NEW"
                image_url=word[3],
                audio_en_url=word[4],
                audio_tr_url=word[5],
                order_number=word[6]
            ))
    
    # AVALANCHE GUARD: Cap at MAX_ITEMS_PER_SESSION (backend authority)
    original_count = len(items)
    if original_count > MAX_ITEMS_PER_SESSION:
        items = items[:MAX_ITEMS_PER_SESSION]
        print(f"⚠️  [AVALANCHE] user={user_id} course={course_id} step={current_step} total={original_count} capped={MAX_ITEMS_PER_SESSION}")
    
    return items, original_count


@router.get("/courses/{course_id}/units/status", response_model=UnitsStatusResponse)
def get_units_status(
    course_id: int,
    user_id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Get unit lock status and progress for a user.
    
    Returns list of units with:
    - Status (OPEN/LOCKED) based on max_open_unit_order
    - Progress (total words, seen words, percentage)
    
    Query params:
        user_id: User ID
    
    Path params:
        course_id: Course ID
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from unit_manager import get_all_units_status
    from api.models import UnitProgressModel, UnitStatusModel
    
    units = get_all_units_status(db, user_id, course_id)
    
    # FORCE UNLOCK MODE (User Request)
    for u in units:
        u["status"] = "OPEN"
    
    # Convert to Pydantic models
    unit_models = []
    for u in units:
        unit_models.append(UnitStatusModel(
            unit_id=u["unit_id"],
            name=u["name"],
            order=u["order"],
            status=u["status"],
            progress=UnitProgressModel(**u["progress"])
        ))
    
    return UnitsStatusResponse(units=unit_models)
