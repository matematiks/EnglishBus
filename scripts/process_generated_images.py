import os
import re
import shutil
from PIL import Image

ARTIFACT_DIR = "/Users/emrah/.gemini/antigravity/brain/3d31a65a-cbac-44b1-bb88-7a51bed8fd5e"
TARGET_DIR = "/Users/emrah/Documents/Projeler/EnglishBus/kurslar/A1_Foundation/images"

def process_images():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        print(f"Created target directory: {TARGET_DIR}")

    files = os.listdir(ARTIFACT_DIR)
    # Pattern: Name_ID_Timestamp.png
    # Example: monday_240_1770456882952.png
    # We want '240.webp'
    
    # Regex to handle names that might have underscores too?
    # Actually, my prompt usage was `ImageName: monday_240`. The tool appends `_timestamp`.
    # So it is `Name_ID_Timestamp.png`.
    # I should look for the last underscore before the extension as timestamp separator, and the one before that as ID separator.
    
    count = 0
    for filename in files:
        if not filename.endswith(".png"):
            continue
            
        # Check if it matches our pattern
        # We look for digits between underscores
        match = re.search(r'_(\d{3})_\d+\.png$', filename)
        if match:
            image_id = match.group(1)
            target_filename = f"{image_id}.webp"
            target_path = os.path.join(TARGET_DIR, target_filename)
            source_path = os.path.join(ARTIFACT_DIR, filename)
            
            print(f"Processing {filename} -> {target_filename}")
            
            try:
                img = Image.open(source_path)
                img.save(target_path, "WEBP", quality=90)
                print(f"Saved to {target_path}")
                
                # Verify it exists
                if os.path.exists(target_path):
                     # Optionally cleanup source or move to a 'processed' folder inside artifacts?
                     # For now, let's just leave it or rename it to indicate processed.
                     done_path = source_path + ".processed"
                     os.rename(source_path, done_path)
                     count += 1
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")
                
    print(f"Processed {count} images.")

if __name__ == "__main__":
    process_images()
