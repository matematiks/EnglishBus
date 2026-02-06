import os
import csv

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPS_FILE = os.path.join(BASE_DIR, "kurslar", "deps 1.text")
OUTPUT_DIR = os.path.join(BASE_DIR, "kurslar", "A1_Foundation")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
AUDIO_EN_DIR = os.path.join(OUTPUT_DIR, "audio") # Using 'audio' as per standard, or 'ing_audio'? 
# Checking kurslar.text earlier: it said /audio/ for English, but then "ADIM 3" said ing_audio vs tr_audio.
# Standard in reimport_all.py seemed to just take filenames.
# Let's stick to the folder structure implied by the previous reimport logic or standard.
# Standard logic in reimport_all.py: 
# word = Word(..., image_url=row.get('image_file'), audio_en_url=row.get('audio_en_file')...)
# It doesn't enforce folder names, just file names.
# Ideally we have `images`, `ing_audio`, `tr_audio`. Let's create those.

def main():
    print(f"Reading from {DEPS_FILE}...")
    
    if not os.path.exists(DEPS_FILE):
        print("Error: Source file not found!")
        return

    # Read words
    with open(DEPS_FILE, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]

    print(f"Found {len(words)} words.")

    # Create directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "ing_audio"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "tr_audio"), exist_ok=True)

    csv_path = os.path.join(OUTPUT_DIR, "words.csv")
    
    print(f"Generating {csv_path}...")
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Headers matching the standard expected by import scripts
        writer.writerow(['id', 'english', 'turkish', 'image_file', 'audio_en_file', 'audio_tr_file'])
        
        for i, word in enumerate(words, 1):
            # Filename formatting: 001.webp, ing_001.mp3, etc.
            idx_str = f"{i:03d}"
            
            # Simple assumption: word is just the English word
            english = word
            turkish = "PENDING"
            
            image_file = f"{idx_str}.webp"
            audio_en_file = f"ing_{idx_str}.mp3"
            audio_tr_file = f"tr_{idx_str}.mp3"
            
            writer.writerow([i, english, turkish, image_file, audio_en_file, audio_tr_file])

            # Create dummy files so import script picks them up
            for fpath, folder in [
                (image_file, IMAGES_DIR),
                (audio_en_file, os.path.join(OUTPUT_DIR, "ing_audio")),
                (audio_tr_file, os.path.join(OUTPUT_DIR, "tr_audio"))
            ]:
                full_path = os.path.join(folder, fpath)
                if not os.path.exists(full_path):
                    with open(full_path, 'wb') as df:
                        pass # Create empty file

    print("Success! Course structure created.")
    print("Next step: Import this course into database.")

if __name__ == "__main__":
    main()
