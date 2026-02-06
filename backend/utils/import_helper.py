import os
import csv
import json
import sys

# Add directory to path to find dictionary_data
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dictionary_data import WORD_TRANSLATIONS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KURSLAR_DIR = os.path.join(BASE_DIR, "kurslar")
PROMPT_FILE = os.path.join(KURSLAR_DIR, "prompt.text")

def load_prompts():
    prompts = {}
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    key, val = line.split(':', 1)
                    prompts[key.strip().lower()] = val.strip()
    return prompts

def convert_text_files():
    prompts = load_prompts()
    print(f"Loaded {len(prompts)} prompts.")

    # Find .text files
    text_files = [f for f in os.listdir(KURSLAR_DIR) if f.endswith('.text') and f != "prompt.text" and f != "kelimeler.text"]
    
    for txt_file in text_files:
        course_name = txt_file.replace('.text', '').replace("deps 1", "Deps 1").replace("pre_A1", "Pre A1")
        course_folder = os.path.join(KURSLAR_DIR, course_name)
        txt_path = os.path.join(KURSLAR_DIR, txt_file)
        
        print(f"Processing {course_name}...")
        
        # Create Folder
        os.makedirs(course_folder, exist_ok=True)
        
        # Output CSV Path
        csv_path = os.path.join(course_folder, "words.csv")
        
        # Read Words
        words = []
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for idx, line in enumerate(lines):
                word = line.strip()
                if not word: continue
                
                # Check for existing prompt (simple case-insensitive match)
                has_prompt = word.lower() in prompts
                image_file = f"{word}.webp" if has_prompt else ""
                
                # Translation lookup
                turkish = WORD_TRANSLATIONS.get(word, WORD_TRANSLATIONS.get(word.lower(), ""))
                
                words.append({
                    "order": idx + 1,
                    "english": word,
                    "turkish": turkish, 
                    "image_file": image_file,
                    "audio_en_file": "",
                    "audio_tr_file": ""
                })
                
        # Write CSV
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            fieldnames = ["order", "english", "turkish", "image_file", "audio_en_file", "audio_tr_file"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(words)
            
        print(f"  -> Created {csv_path} with {len(words)} words.")

if __name__ == "__main__":
    convert_text_files()
