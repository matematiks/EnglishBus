import os
import sys
import sqlite3
import csv
import shutil

# Setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KURSLAR_DIR = os.path.join(BASE_DIR, "kurslar")
DB_PATH = os.path.join(BASE_DIR, "englishbus.db")

def main():
    print(f"Connecting to database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get Courses
    courses = cursor.execute("SELECT id, name FROM Courses").fetchall()
    
    if not courses:
        print("No courses found in database.")
        return

    print(f"Found {len(courses)} courses in database.")

    for course_id, course_name in courses:
        safe_name = course_name.replace(" ", "_").replace("/", "-")
        course_folder = os.path.join(KURSLAR_DIR, safe_name)
        
        print(f"Reconstructing '{course_name}' -> {course_folder}")
        
        if not os.path.exists(course_folder):
            os.makedirs(course_folder)

        # Get Words
        words = cursor.execute("""
            SELECT english, turkish, image_url, audio_en_url, audio_tr_url, order_number 
            FROM Words 
            WHERE course_id = ? 
            ORDER BY order_number
        """, (course_id,)).fetchall()

        if not words:
            print(f"  Warning: No words for course {course_name}")
            continue

        csv_path = os.path.join(course_folder, "words.csv")
        
        # Write CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Headers matching standard
            writer.writerow(['id', 'english', 'turkish', 'image_file', 'audio_en_file', 'audio_tr_file'])
            
            for w in words:
                # w: eng, tr, img, aud_en, aud_tr, ord
                # Clean paths to filenames only if they are full paths or /assets/...
                img = os.path.basename(w[2]) if w[2] else ""
                aud_en = os.path.basename(w[3]) if w[3] else ""
                aud_tr = os.path.basename(w[4]) if w[4] else ""
                
                writer.writerow([w[5], w[0], w[1], img, aud_en, aud_tr])
        
        print(f"  Saved {len(words)} words to words.csv")

    conn.close()
    print("\nReconstruction Complete! You can now see these courses in Admin > Scan.")

if __name__ == "__main__":
    main()
