import sys
import os
import sqlite3
import pandas as pd

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

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    db = SessionLocal()
    
    # Create Course
    course = Course(name=course_name, total_words=len(df))
    db.add(course)
    db.commit()
    db.refresh(course)

    # Create Units and Import Words
    WORDS_PER_UNIT = 50
    current_unit = None
    words_to_add = []
    
    for index, row in df.iterrows():
        # Check if we need a new unit
        if index % WORDS_PER_UNIT == 0:
            unit_order = (index // WORDS_PER_UNIT) + 1
            unit_name = f"Unit {unit_order}"
            
            # Calculate word count for this unit (min of 50 or remaining)
            remaining_words = len(df) - index
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

        # Handle different CSV structures if necessary (some have 'order', some 'id')
        english = row.get('english', row.get('English', '')).strip()
        turkish = row.get('turkish', row.get('Turkish', '')).strip()
        
        # Construct absolute URLs for frontend based on static mount (/assets -> /kurslar)
        image_file = row.get('image_file', None)
        audio_en_file = row.get('audio_en_file', None)
        audio_tr_file = row.get('audio_tr_file', None)

        # Base URL for A1 Foundation
        base_url = "/assets/A1_Foundation"
        
        word = Word(
            course_id=course.id,
            unit_id=current_unit.id,
            english=english,
            turkish=turkish,
            # Prepend path if file exists
            image_url=f"{base_url}/images/{image_file}" if image_file and not str(image_file).startswith("http") else image_file,
            audio_en_url=f"{base_url}/ing_audio/{audio_en_file}" if audio_en_file and not str(audio_en_file).startswith("http") else audio_en_file,
            audio_tr_url=f"{base_url}/tr_audio/{audio_tr_file}" if audio_tr_file and not str(audio_tr_file).startswith("http") else audio_tr_file,
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
    
    # Delete dependent tables first
    db.execute(text("DELETE FROM UserWordProgress")) 
    db.execute(text("DELETE FROM UserProgress"))     
    db.execute(text("DELETE FROM UserCourseProgress"))
    
    # Then delete content tables
    db.execute(text("DELETE FROM Words"))
    db.execute(text("DELETE FROM Units"))
    db.execute(text("DELETE FROM Courses"))
    
    # Try to reset sequences (might fail if table empty/fresh)
    try:
        db.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'Words'"))
        db.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'Units'"))
        db.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'Courses'"))
    except Exception:
        pass

    db.commit()
    db.close()

    # 2. Import Courses
    courses_dir = os.path.join(BASE_DIR, "kurslar")
    
    # A1 Foundation (Only available course for now)
    import_course(os.path.join(courses_dir, "A1_Foundation"), "A1 Foundation")


    print("\nAll imports completed!")

if __name__ == "__main__":
    main()
