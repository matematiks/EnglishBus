import os
import sys
import pandas as pd
import sqlite3
import argparse
from pathlib import Path

# Database setup
# Database setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "englishbus.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def import_course(course_folder_path, course_name, force=False):
    print(f"🚀 Starting import for course: {course_name}")
    print(f"📁 Folder: {course_folder_path}")
    
    path = Path(course_folder_path)
    if not path.exists():
        print(f"❌ Error: Folder not found: {course_folder_path}")
        return

    # 1. Find Word List (Excel or CSV)
    data_file = None
    for ext in ['*.xlsx', '*.xls', '*.csv']:
        files = list(path.glob(ext))
        if files:
            data_file = files[0]
            break
    
    if not data_file:
        print("❌ Error: No Excel or CSV file found in folder (words.xlsx or words.csv)")
        return
        
    print(f"📄 Found data file: {data_file.name}")
    
    # 2. Read Data
    try:
        if data_file.suffix == '.csv':
            df = pd.read_csv(data_file)
        else:
            df = pd.read_excel(data_file)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    # Normalize columns
    df.columns = [c.lower().strip() for c in df.columns]
    required = ['english', 'turkish']
    for col in required:
        if col not in df.columns:
            print(f"❌ Error: Missing required column '{col}'")
            return
            
    # 3. Connect to DB
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if course exists
    cursor.execute("SELECT id FROM Courses WHERE name = ?", (course_name,))
    existing = cursor.fetchone()
    
    if existing:
        if force:
            print(f"⚠️ Course '{course_name}' exists. Deleting old data...")
            course_id = existing[0]
            cursor.execute("DELETE FROM Words WHERE course_id = ?", (course_id,))
            cursor.execute("DELETE FROM Units WHERE course_id = ?", (course_id,))
            cursor.execute("DELETE FROM Courses WHERE id = ?", (course_id,))
            conn.commit()
        else:
            print(f"⚠️ Course '{course_name}' already exists. Use --force to overwrite.")
            return

    # Create Course
    cursor.execute("INSERT INTO Courses (name, total_words) VALUES (?, ?)", (course_name, len(df)))
    course_id = cursor.lastrowid
    print(f"✅ Created Course: {course_name} (ID: {course_id})")
    
    # 4. Process Words & Units
    UNIT_SIZE = 50
    
    words_processed = 0
    units_created = 0
    
    # Prepare asset paths bases
    # Assets are served from /assets URL which maps to kurslar/ folder
    # URL format: /assets/{Folder_Name}/{Subfolder}/{File}
    folder_name = path.name # e.g., A1_English
    
    for i, row in df.iterrows():
        english = str(row['english']).strip()
        turkish = str(row['turkish']).strip()
        
        # Calculate Unit
        unit_order = (i // UNIT_SIZE) + 1
        unit_name = f"{course_name} - Unit {unit_order}"
        
        # Create Unit if new
        cursor.execute("SELECT id FROM Units WHERE course_id = ? AND order_number = ?", (course_id, unit_order))
        unit_row = cursor.fetchone()
        
        if not unit_row:
            cursor.execute("INSERT INTO Units (course_id, name, order_number, word_count) VALUES (?, ?, ?, 0)", 
                           (course_id, unit_name, unit_order))
            unit_id = cursor.lastrowid
            units_created += 1
            print(f"   Created Unit {unit_order}")
        else:
            unit_id = unit_row[0]
            
        # Match Assets
        # Priority: Use filename from CSV columns if available
        
        # 1. Image
        image_url = None
        csv_image = str(row.get('image_file', '')).strip()
        if csv_image and csv_image != 'nan':
            # Check if exists
            if (path / "images" / csv_image).exists():
                image_url = f"/assets/{folder_name}/images/{csv_image}"
        
        if not image_url:
            # Fallback to ID based convention
            file_id = row.get('id', i + 1)
            img_candidates = [f"{file_id:03}.webp", f"{file_id:03}.jpg", f"{file_id:03}.png", f"{file_id}.jpg"]
            for fname in img_candidates:
                if (path / "images" / fname).exists():
                    image_url = f"/assets/{folder_name}/images/{fname}"
                    break
                    
        # 2. Audio EN
        audio_en_url = None
        csv_audio_en = str(row.get('audio_en_file', '')).strip()
        if csv_audio_en and csv_audio_en != 'nan':
             if (path / "ing_audio" / csv_audio_en).exists():
                audio_en_url = f"/assets/{folder_name}/ing_audio/{csv_audio_en}"
        
        if not audio_en_url:
            file_id = row.get('id', i + 1)
            audio_en_candidates = [f"ing_{file_id:03}.mp3", f"en_{file_id:03}.mp3", f"{file_id:03}.mp3"]
            for fname in audio_en_candidates:
                if (path / "ing_audio" / fname).exists():
                    audio_en_url = f"/assets/{folder_name}/ing_audio/{fname}"
                    break
        
        # 3. Audio TR
        audio_tr_url = None
        csv_audio_tr = str(row.get('audio_tr_file', '')).strip()
        if csv_audio_tr and csv_audio_tr != 'nan':
             if (path / "tr_audio" / csv_audio_tr).exists():
                audio_tr_url = f"/assets/{folder_name}/tr_audio/{csv_audio_tr}"
        
        if not audio_tr_url:
            # Fallback
            file_id = row.get('id', i + 1)
            audio_tr_candidates = [f"tr_{file_id:03}.mp3"]
            for fname in audio_tr_candidates:
                if (path / "tr_audio" / fname).exists():
                    audio_tr_url = f"/assets/{folder_name}/tr_audio/{fname}"
                    break
        
        # Insert Word
        cursor.execute("""
            INSERT INTO Words 
            (course_id, unit_id, english, turkish, image_url, audio_en_url, audio_tr_url, order_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (course_id, unit_id, english, turkish, image_url, audio_en_url, audio_tr_url, i+1))
        
        # Update Unit Count
        cursor.execute("UPDATE Units SET word_count = word_count + 1 WHERE id = ?", (unit_id,))
        
        words_processed += 1
        
    conn.commit()
    conn.close()
    
    print("-" * 50)
    print(f"🎉 Import Complete!")
    print(f"📚 Course: {course_name}")
    print(f"📦 Units: {units_created}")
    print(f"📖 Words: {words_processed}")
    print("-" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EnglishBus Course Importer")
    parser.add_argument("folder", help="Path to course folder")
    parser.add_argument("--name", help="Course Name (defaults to folder name)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing course")
    
    args = parser.parse_args()
    
    c_name = args.name if args.name else Path(args.folder).name
    
    import_course(args.folder, c_name, args.force)
