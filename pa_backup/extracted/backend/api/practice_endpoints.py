from fastapi import APIRouter, Depends, Query
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.dependencies import get_db
from features.sentence_generator import sentence_engine

router = APIRouter()

@router.get("/sentences")
def get_practice_sentences(
    user_id: int, 
    course_id: int, 
    word_count: int = Query(None, description="Simulated progress: Use only first N words"),
    limit: int = 5,
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Generate dynamic sentences based on the words the user has learned.
    If 'word_count' is provided, it simulates the user knowing only the first N words.
    Otherwise, it uses all words available in the course (or theoretically user's progress).
    """
    
    # 1. Fetch ALL words in order
    cursor = db.execute("""
        SELECT english FROM Words 
        WHERE course_id = ? 
        ORDER BY order_number ASC
    """, (course_id,))
    
    all_words = [r[0] for r in cursor.fetchall()]
    
    # 2. Filter based on progress (UserWordProgress)
    if word_count is not None:
        # Simulation mode
        known_words = all_words[:word_count]
    else:
        # Real gathered progress
        # Get IDs of words the user has learned (repetition_count > 0 or present in progress)
        # We can join with UserWordProgress or UserProgress
        # Assuming UserProgress tracks learning state
        cursor = db.execute("""
            SELECT w.english 
            FROM Words w
            JOIN UserProgress up ON w.id = up.word_id
            WHERE up.user_id = ? AND w.course_id = ?
            ORDER BY w.order_number ASC
        """, (user_id, course_id))
        
        known_words = [r[0] for r in cursor.fetchall()]
        
        # Fallback if no progress (e.g. testing) -> return empty or first few?
        # User requirement: "learned words". If none learned, no sentences.
        if not known_words:
             # AUTO-fallback for demo if completely empty (optional, but safer to be strict per request)
             # "sistemi sıfırladığımızda öğrenilmiş tüm kelimler silinmeli. cümle oluşturma hafızasından da silinmeli."
             # So strict empty is better.
             pass

    if not known_words:
        return {"sentences": [], "message": "No words found or limit is 0."}

    # 3. Generate
    sentences = sentence_engine.generate(known_words, count=limit)
    
    return {
        "status": "success",
        "word_count_used": len(known_words),
        "last_word": known_words[-1] if known_words else None,
        "sentences": sentences
    }
