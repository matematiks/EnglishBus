
import sys
import os
import csv
import sqlite3

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from sqlalchemy import text
from backend.database import SessionLocal, Course, Unit, Word, Base, engine

def import_course(directory, course_name):
    print(f"Importing {course_name} from {directory}...")
    
    csv_path = os.path.join(directory, "words.csv")
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    rows = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    db = SessionLocal()
    
    # Create Course
    course = Course(name=course_name, total_words=len(rows))
    db.add(course)
    db.commit()
    db.refresh(course)

    # Create Units and Import Words
    WORDS_PER_UNIT = 50
    current_unit = None
    words_to_add = []
    
    for index, row in enumerate(rows):
        # Check if we need a new unit
        if index % WORDS_PER_UNIT == 0:
            unit_order = (index // WORDS_PER_UNIT) + 1
            unit_name = f"Unit {unit_order}"
            
            # Calculate word count for this unit (min of 50 or remaining)
            remaining_words = len(rows) - index
            current_unit_word_count = min(WORDS_PER_UNIT, remaining_words)
            
            current_unit = Unit(
                course_id=course.id, 
                name=unit_name, 
                order_number=unit_order, 
                word_count=current_unit_word_count
            )
            db.add(current_unit)
            db.commit()
            db.refresh(current_unit)
            print(f"  -> Created {unit_name} ({current_unit_word_count} words)")

        # Handle different CSV structures (case sensitivity)
        english = (row.get('english') or row.get('English') or '').strip()
        turkish = (row.get('turkish') or row.get('Turkish') or '').strip()
        
        # Construct absolute URLs for frontend based on static mount (/assets -> /kurslar)
        image_file = row.get('image_file', None)
        audio_en_file = row.get('audio_en_file', None)
        audio_tr_file = row.get('audio_tr_file', None)

        # Base URL for A1 Foundation
        base_url = "/assets/A1_Foundation"
        
        # Helper to format URL
        def format_url(base, filename):
            if filename and filename.strip() and not filename.startswith("http"):
                return f"{base}/{filename}"
            return filename

        word = Word(
            course_id=course.id,
            unit_id=current_unit.id,
            english=english,
            turkish=turkish,
            image_url=format_url(f"{base_url}/images", image_file),
            audio_en_url=format_url(f"{base_url}/ing_audio", audio_en_file),
            audio_tr_url=format_url(f"{base_url}/tr_audio", audio_tr_file),
            order_number=index + 1
        )
        words_to_add.append(word)

    db.add_all(words_to_add)
    db.commit()
    print(f"Successfully imported {len(words_to_add)} words into {course_name}.")
    db.close()

def main():
    # 0. Ensure tables exist
    print("Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    # 1. Clear existing course data (Order matches FK constraints)
    print("Clearing existing course data...")
    db = SessionLocal()
    
    try:
        # Delete dependent tables first
        db.execute(text("DELETE FROM UserWordProgress")) 
        db.execute(text("DELETE FROM UserProgress"))     
        db.execute(text("DELETE FROM UserCourseProgress"))
        
        # Then delete content tables
        db.execute(text("DELETE FROM Words"))
        db.execute(text("DELETE FROM Units"))
        db.execute(text("DELETE FROM Courses"))
        
        db.commit()
    except Exception as e:
        print(f"Error clearing data: {e}")
        db.rollback()

    # Try to reset sequences (might fail if table empty/fresh)
    try:
        db.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'Words'"))
        db.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'Units'"))
        db.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'Courses'"))
        db.commit()
    except Exception:
        pass

    db.close()

    # 2. Import Courses
    courses_dir = os.path.join(BASE_DIR, "kurslar")
    
    # A1 Foundation (Only available course for now)
    course_path = os.path.join(courses_dir, "A1_Foundation")
    if os.path.exists(course_path):
        import_course(course_path, "A1 Foundation")
    else:
        print(f"Warning: Course directory not found at {course_path}")

    print("\nAll imports completed!")

if __name__ == "__main__":
    main()
