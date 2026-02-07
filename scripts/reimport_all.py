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

    # Create Unit (Single unit for now as per previous logic)
    unit = Unit(course_id=course.id, name="Unit 1", order_number=1, word_count=len(df))
    db.add(unit)
    db.commit()
    db.refresh(unit)

    # Import Words
    words_to_add = []
    for index, row in df.iterrows():
        # Handle different CSV structures if necessary (some have 'order', some 'id')
        english = row.get('english', row.get('English', '')).strip()
        turkish = row.get('turkish', row.get('Turkish', '')).strip()
        
        word = Word(
            course_id=course.id,
            unit_id=unit.id,
            english=english,
            turkish=turkish,
            image_url=row.get('image_file', None),
            audio_en_url=row.get('audio_en_file', None),
            audio_tr_url=row.get('audio_tr_file', None),
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

    # 1. Clear existing course data
    print("Clearing existing course data...")
    db = SessionLocal()
    db.execute(text("DELETE FROM Words"))
    db.execute(text("DELETE FROM Units"))
    db.execute(text("DELETE FROM Courses"))
    db.execute(text("DELETE FROM UserWordProgress")) # Clear progress to avoid orphans
    db.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'Words'"))
    db.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'Units'"))
    db.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'Courses'"))
    db.commit()
    db.close()

    # 2. Import Courses
    courses_dir = os.path.join(BASE_DIR, "kurslar")
    
    # A1 English
    import_course(os.path.join(courses_dir, "A1_English"), "A1 English")
    
    # Numbers
    import_course(os.path.join(courses_dir, "Numbers"), "Numbers")
    
    # First Words
    import_course(os.path.join(courses_dir, "First Words"), "First Words")

    print("\nAll imports completed!")

if __name__ == "__main__":
    main()
