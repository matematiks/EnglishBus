
import os
import shutil
import sys

# Define identifying directories and files to clean
CLEANUP_TARGETS = [
    "pa_backup",
    "yedekler",
    "EnglishBus",  # The recursive one
    ".git",        # OPTIONAL: Only if user REALLY needs space and doesn't need git history
    "frontend/node_modules",
    "__pycache__",
    ".pytest_cache"
]

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                except:
                    pass
    return total_size

def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

def cleanup():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"🧹 Starting cleanup in: {base_dir}")
    
    deleted_size = 0

    # 1. Targets
    for target in CLEANUP_TARGETS:
        path = os.path.join(base_dir, target)
        
        # Handle recursive finding of __pycache__
        if target == "__pycache__":
            for root, dirs, files in os.walk(base_dir):
                for d in dirs:
                    if d == "__pycache__":
                        p = os.path.join(root, d)
                        try:
                            s = get_size(p)
                            shutil.rmtree(p)
                            deleted_size += s
                            print(f"   - Removed cache: {p} ({human_readable_size(s)})")
                        except Exception as e:
                            print(f"   ! Error removing {p}: {e}")
            continue

        if os.path.exists(path):
            try:
                size = get_size(path)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                deleted_size += size
                print(f"✅ Removed: {target} ({human_readable_size(size)})")
            except Exception as e:
                print(f"❌ Error removing {target}: {e}")
        else:
           # print(f"   (Not found: {target})") 
           pass
           
    print(f"\n🎉 Total space reclaimed: {human_readable_size(deleted_size)}")
    print("\n⚠️  IMPORTANT NEXT STEPS FOR DISK SPACE:")
    print("1. If you still need more space, re-install dependencies minimally:")
    print("   rm -rf .venv")
    print("   python3 -m venv .venv")
    print("   source .venv/bin/activate")
    print("   pip install --no-cache-dir -r requirements_minimal.txt")
    print("--------------------------------------------------")

if __name__ == "__main__":
    confirmation = input("⚠️  This will delete backup folders, caches, and node_modules. Are you sure? (y/n): ")
    if confirmation.lower() == 'y':
        cleanup()
    else:
        print("Operation cancelled.")
