import os
import csv
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDS_CSV = os.path.join(BASE_DIR, "kurslar", "A1_Foundation", "words.csv")
IMAGES_DIR = os.path.join(BASE_DIR, "kurslar", "A1_Foundation", "images")
MISSING_REPORT_TEXT = os.path.join(BASE_DIR, "kurslar", "MISSING_IMAGES.txt")

def generate_missing_list():
    if not os.path.exists(WORDS_CSV):
        print(f"Error: {WORDS_CSV} not found.")
        return

    # 1. Read CSV to see what images are EXPECTED
    words = []
    with open(WORDS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            words.append(row)

    # 2. Check what files actually exist in the images folder
    existing_files = set(os.listdir(IMAGES_DIR))
    
    missing_items = []
    
    for row in words:
        english = row.get("english", "").strip()
        image_file = row.get("image_file", "").strip()
        
        # Condition 1: File physically missing
        if image_file not in existing_files:
            missing_items.append(english)
            continue
            
        # Condition 2: File exists but is a placeholder (numeric name like 001.webp)
        # We assume that if we successfully moved a real image, it would be named 'apple.png' etc.
        # So anything matching NNN.webp is likely still a placeholder we didn't fill.
        # (Unless we specifically decided to rename real images to NNN.webp, but the user asked 
        # to carry them "isimlerini değiştirmeden" - without changing names).
        
        if re.match(r"^\d{3}\.webp$", image_file):
            # It's a placeholder name. Did we fail to update it?
            # Yes, because if we updated it, it would be "apple.png" in the CSV.
            missing_items.append(english)
            
    # Remove duplicates and save
    missing_items = sorted(list(set(missing_items)))
    
    with open(MISSING_REPORT_TEXT, "w", encoding='utf-8') as f:
        f.write("\n".join(missing_items))
        
    print(f"Found {len(missing_items)} missing images (either no file or still placeholder).")
    print(f"List saved to: {MISSING_REPORT_TEXT}")
    
    # Print preview
    print("-" * 20)
    for w in missing_items[:20]:
        print(w)
    if len(missing_items) > 20:
        print(f"... and {len(missing_items)-20} more.")
    print("-" * 20)

if __name__ == "__main__":
    generate_missing_list()
