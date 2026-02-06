import os
import shutil

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "kurslar", "imagSes")
DEST_DIR = os.path.join(BASE_DIR, "kurslar", "imagJYGes")

def get_unique_filename(directory, filename):
    """
    Returns a unique filename. If filename exists in directory,
    appends _1, _2, etc. until a unique name is found.
    Example: apple.png -> apple_1.png
    """
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
        
    return new_filename

def merge_directories():
    if not os.path.exists(SRC_DIR):
        print(f"Source directory not found: {SRC_DIR}")
        return

    if not os.path.exists(DEST_DIR):
        print(f"Destination directory not found: {DEST_DIR}, creating it.")
        os.makedirs(DEST_DIR, exist_ok=True)

    files = os.listdir(SRC_DIR)
    print(f"Found {len(files)} files in {SRC_DIR}...")
    
    moved_count = 0
    for filename in files:
        src_path = os.path.join(SRC_DIR, filename)
        
        # Skip directories if any
        if os.path.isdir(src_path):
            continue
            
        # Determine unique destination name
        unique_name = get_unique_filename(DEST_DIR, filename)
        dest_path = os.path.join(DEST_DIR, unique_name)
        
        # Move file
        shutil.move(src_path, dest_path)
        print(f"Moved: {filename} -> {unique_name}")
        moved_count += 1
        
    print(f"\nMerge Complete! Moved {moved_count} files.")
    
    # Optional: remove source dir if empty
    if not os.listdir(SRC_DIR):
        os.rmdir(SRC_DIR)
        print(f"Removed empty source directory: {SRC_DIR}")
    else:
        print(f"Source directory {SRC_DIR} is not empty (subdirs?), kept.")

if __name__ == "__main__":
    merge_directories()
