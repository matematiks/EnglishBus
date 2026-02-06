import os
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDS_CSV = os.path.join(BASE_DIR, "kurslar", "A1_Foundation", "words.csv")
DEST_IMG_DIR = os.path.join(BASE_DIR, "kurslar", "A1_Foundation", "images")
MISSING_REPORT_TEXT = os.path.join(BASE_DIR, "kurslar", "MISSING_IMAGES.txt")

def report_missing_images():
    rows = []
    with open(WORDS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            
    missing_list = []
    
    # Get list of existing image files in destination
    # Note: filenames might be 001.webp but content is png, irrelevant for existence check
    existing_files = set(os.listdir(DEST_IMG_DIR))
    
    # BUT, we might have copied 002.webp but 001.webp is missing.
    # Wait, the copy script handles the copy. If src was missing, dest is missing.
    # The user wants to know WHICH words are missing images.
    
    # We can check if the DEST file exists.
    # BUT: The previous script outputted "MISSING: ...".
    # And we also know that placeholders might exist if I didn't clean the dest dir first?
    # Actually, init_new_course created placeholders (maybe?).
    # Let's check if the file size is very small (placeholder) or if it's a real copied image.
    # Or, rely on the fact that I just ran the copy script and if source wasn't found, 
    # the destination file might be the old placeholder (if it existed) or non-existent.
    
    # Let's check against SOURCE again to be sure what is truly missing from SOURCE.
    # Because init_new_course might have put dummy images.
    
    # Actually, the user asked "eksik olan kelimeler hangileri".
    # I should check which words failed to find a source match.
    
    # Let's re-run the logic of matching but only output missing.
    
    SOURCE_IMG_DIR = os.path.join(BASE_DIR, "kurslar", "images")
    
    print("Checking for missing images...")
    
    for row in rows:
        english_word = row.get("english", "").strip()
        if not english_word: continue
        
        # Check source
        potential_names = [
            f"{english_word}.png",
            f"{english_word}.webp",
            f"{english_word}.jpg",
            f"{english_word}.jpeg"
        ]
        
        found = False
        for p_name in potential_names:
            if os.path.exists(os.path.join(SOURCE_IMG_DIR, p_name)):
                found = True
                break
        
        if not found:
            missing_list.append(english_word)

    # Write report
    with open(MISSING_REPORT_TEXT, "w", encoding='utf-8') as f:
        f.write("\n".join(missing_list))
    
    print(f"Found {len(missing_list)} missing images.")
    print(f"List saved to: {MISSING_REPORT_TEXT}")
    
    # Also print to stdout for tool output capture
    print("-" * 20)
    for w in missing_list:
        print(w)
    print("-" * 20)

if __name__ == "__main__":
    report_missing_images()
