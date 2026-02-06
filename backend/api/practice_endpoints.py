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
    
    # 1. Fetch learned words for this user and course (repetition_count > 0)
    cursor = db.execute("""
        SELECT w.english, up.repetition_count
        FROM Words w
        JOIN UserProgress up ON w.id = up.word_id
        WHERE up.user_id = ? AND w.course_id = ? AND up.repetition_count > 0
        ORDER BY w.order_number ASC
    """, (user_id, course_id))
    rows = cursor.fetchall()
    if not rows:
        # Final fallback: ignore course_id entirely and get any learned words for the user
        cursor = db.execute("""
            SELECT w.english, up.repetition_count
            FROM Words w
            JOIN UserProgress up ON w.id = up.word_id
            WHERE up.user_id = ? AND up.repetition_count > 0
            ORDER BY w.order_number ASC
        """, (user_id,))
        rows = cursor.fetchall()
    known_words = [r[0] for r in rows]
    # Store repetition counts for later level mapping (optional, we will recompute later)
    # known_reps = {r[0]: r[1] for r in rows}


    # 2. Optional simulation mode: limit to first N words if word_count provided
    if word_count is not None:
        known_words = known_words[:word_count]

    if not known_words:
        return {"sentences": [], "message": "No words found or limit is 0."}

    # 3. Generate
    raw_sentences = sentence_engine.generate(known_words, count=limit)
    if not raw_sentences:
        # No fallback. Return explicit status so frontend can handle it natively.
        return {
            "status": "insufficient_vocabulary", 
            "message": "Not enough words to generate meaningful sentences.",
            "sentences": []
        }
    
    # 4. Translate & Format with Audio Links
    from googletrans import Translator
    import urllib.parse
    
    translator = Translator()
    formatted_sentences = []
    
    # Phase 12 Debug Wrapper
    try:
        for sent_obj in raw_sentences:
            # Phase 12: sent_obj is now {'text': str, 'key_word': str}
            en_text = sent_obj.get('text', '')
            key_word = sent_obj.get('key_word')
            
            try:
                # Translate to Turkish
                tr_translation = translator.translate(en_text, src='en', dest='tr').text
            except Exception as e:
                print(f"Translation Error: {e}")
                tr_translation = "(Çeviri oluşturulamadı)"
                
            # Image Fetch based on Key Word
            image_url = None
            if key_word:
                # Look up image_file for this key word (case-insensitive)
                # We assume word is in DB if it came from generator, but casing might differ
                cur_img = db.execute("SELECT image_url FROM Words WHERE english LIKE ? LIMIT 1", (key_word,))
                row_img = cur_img.fetchone()
                if row_img and row_img[0]:
                    raw_path = row_img[0]
                    if raw_path.startswith("/") or raw_path.startswith("http"):
                         image_url = raw_path
                    else:
                         image_url = f"/assets/images/{raw_path}"

            # Enhance Object
            formatted_sentences.append({
                "english": en_text,
                "turkish": tr_translation,
                "image_url": image_url, # New Field
                "key_word": key_word,   # New Field (Debug/UI info)
                # Link to our new dynamic TTS endpoint
                "audio_en_url": f"/audio/tts?lang=en&text={urllib.parse.quote(en_text)}",
                "audio_tr_url": f"/audio/tts?lang=tr&text={urllib.parse.quote(tr_translation)}",
                "is_sentence": True
            })
    except Exception as e:
        import traceback
        return {"status": "error", "message": f"Server Logic Error: {str(e)}", "trace": traceback.format_exc()}
        
    # After generating formatted_sentences, add levels mapping
    
    # After generating formatted_sentences, add levels mapping
    # Fetch repetition counts for each known word
    cursor = db.execute("""
        SELECT w.english, up.repetition_count
        FROM Words w
        JOIN UserProgress up ON w.id = up.word_id
        WHERE up.user_id = ? AND up.repetition_count > 0
    """, (user_id,))
    level_map = {row[0]: level_from_reps(row[1]) for row in cursor.fetchall()}

    # Compute counts per level
    counts = {"new": 0, "beginner": 0, "middle": 0, "advanced": 0, "expert": 0}
    for lvl in level_map.values():
        if lvl == "Yeni":
            counts["new"] += 1
        elif lvl == "Başlangıç":
            counts["beginner"] += 1
        elif lvl == "Orta":
            counts["middle"] += 1
        elif lvl == "İleri":
            counts["advanced"] += 1
        else:
            counts["expert"] += 1

    return {
        "status": "success",
        "word_count_used": len(known_words),
        "last_word": known_words[-1] if known_words else None,
        "sentences": formatted_sentences,
        "levels": level_map,
        "counts": counts,
        "debug_known_words": known_words,
        "debug_raw_sentences": raw_sentences
    }

def level_from_reps(reps: int) -> str:
    if reps == 0:
        return "Yeni"
    if 1 <= reps <= 5:
        return "Başlangıç"
    if 6 <= reps <= 10:
        return "Orta"
    if 11 <= reps <= 20:
        return "İleri"
    return "Usta"
