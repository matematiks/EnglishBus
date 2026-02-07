import os
import shutil
from PIL import Image
from pathlib import Path

# Paths
SOURCE_DIR = "kurslar/A1_Foundation/images"
BACKUP_DIR = "kurslar/A1_Foundation/images_backup"
TARGET_WIDTH = 800
QUALITY = 70

def optimize_images():
    # 1. Create Backup
    if not os.path.exists(BACKUP_DIR):
        print(f"📦 Creating backup at {BACKUP_DIR}...")
        try:
            shutil.copytree(SOURCE_DIR, BACKUP_DIR)
            print("✅ Backup successful")
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return
    else:
        print(f"ℹ️ Backup already exists at {BACKUP_DIR}, skipping copy.")

    # 2. Process Images
    files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    total_files = len(files)
    print(f"🔄 Processing {total_files} images...")

    saved_space = 0
    processed_count = 0

    for filename in files:
        filepath = os.path.join(SOURCE_DIR, filename)
        
        try:
            # Measure original size
            original_size = os.path.getsize(filepath)
            
            with Image.open(filepath) as img:
                # Convert RGBA to RGB if saving as JPEG (Pillow requirement)
                # But we keep original extension. If PNG has alpha, keep it.
                # If resizing:
                width, height = img.size
                
                if width > TARGET_WIDTH:
                    # Calculate new height to maintain aspect ratio
                    new_height = int((TARGET_WIDTH / width) * height)
                    img = img.resize((TARGET_WIDTH, new_height), Image.Resampling.LANCZOS)
                
                # Verify mode for saving
                if img.mode in ("RGBA", "P") and filename.lower().endswith('.jpg'):
                    img = img.convert("RGB")

                # Save with optimization
                # For PNG, optimize=True attemptszlib compression
                # For JPEG, quality controls lossy compression
                # Save as WebP
                webp_path = os.path.splitext(filepath)[0] + ".webp"
                img.save(webp_path, "WEBP", quality=QUALITY)
                
            # Close image
            img.close()
            
            # Remove original if it wasn't webp
            if not filename.lower().endswith('.webp'):
                os.remove(filepath)

            # Measure new size
            new_size = os.path.getsize(webp_path)
            saved = original_size - new_size
            saved_space += saved
            processed_count += 1
            
            print(f"  ✓ {filename}: {original_size/1024:.1f}KB -> {new_size/1024:.1f}KB (Saved {saved/1024:.1f}KB)")
            
        except Exception as e:
            print(f"  ❌ Error processing {filename}: {e}")

    # Summary
    print("\n" + "="*40)
    print(f"🎉 Optimization Complete!")
    print(f"Files Processed: {processed_count}/{total_files}")
    print(f"Total Space Saved: {saved_space / (1024*1024):.2f} MB")
    print("="*40)

if __name__ == "__main__":
    optimize_images()
