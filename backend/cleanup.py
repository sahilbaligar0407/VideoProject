"""
Cleanup script to remove unnecessary files from the codebase.
Removes outputs, cache, temp files, test files, and debug files.
"""

import os
import shutil
import glob

def cleanup_directory(dir_path, pattern="*", description=""):
    """Clean up files in a directory matching a pattern"""
    if not os.path.exists(dir_path):
        print(f"Directory does not exist: {dir_path}")
        return 0
    
    count = 0
    for file_path in glob.glob(os.path.join(dir_path, pattern)):
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                count += 1
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                count += 1
        except Exception as e:
            print(f"Failed to remove {file_path}: {e}")
    
    if count > 0:
        print(f"{description}: Removed {count} file(s)")
    else:
        print(f"{description}: No files to remove")
    
    return count

def cleanup_pycache():
    """Remove all __pycache__ directories"""
    count = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                count += 1
            except Exception as e:
                print(f"Failed to remove {pycache_path}: {e}")
    
    if count > 0:
        print(f"Removed {count} __pycache__ directory(ies)")
    else:
        print("No __pycache__ directories to remove")
    
    return count

def main():
    """Main cleanup function"""
    print("Starting cleanup...")
    print("=" * 50)
    
    total_removed = 0
    
    # Clean up output files (keep directory structure)
    print("\nCleaning outputs directory...")
    total_removed += cleanup_directory("outputs", "*", "Output files")
    
    # Clean up upload files
    print("\nCleaning uploads directory...")
    total_removed += cleanup_directory("uploads", "*", "Upload files")
    
    # Clean up temp files
    print("\nCleaning temp directory...")
    total_removed += cleanup_directory("temp", "*", "Temp files")
    
    # Clean up cache files
    print("\nCleaning cache/embeddings directory...")
    total_removed += cleanup_directory("cache/embeddings", "*.pkl", "Cache files")
    
    # Clean up test files
    print("\nCleaning test files...")
    test_files = glob.glob("test_*.py")
    for test_file in test_files:
        try:
            os.remove(test_file)
            total_removed += 1
        except Exception as e:
            print(f"Failed to remove {test_file}: {e}")
    if test_files:
        print(f"Removed {len(test_files)} test file(s)")
    else:
        print("No test files to remove")
    
    # Clean up debug files
    print("\nCleaning debug files...")
    debug_files = glob.glob("debug_*.py")
    for debug_file in debug_files:
        try:
            os.remove(debug_file)
            total_removed += 1
        except Exception as e:
            print(f"Failed to remove {debug_file}: {e}")
    if debug_files:
        print(f"Removed {len(debug_files)} debug file(s)")
    else:
        print("No debug files to remove")
    
    # Clean up test assets
    print("\nCleaning test assets...")
    test_assets = ["proof_frame.png", "test_simple.srt", "test_clean.srt"]
    for asset in test_assets:
        if os.path.exists(asset):
            try:
                os.remove(asset)
                total_removed += 1
                print(f"Removed {asset}")
            except Exception as e:
                print(f"Failed to remove {asset}: {e}")
    
    # Clean up __pycache__ directories
    print("\nCleaning __pycache__ directories...")
    total_removed += cleanup_pycache()
    
    # Clean up database file (optional - comment out if you want to keep it)
    print("\nCleaning database file...")
    db_files = ["app/db/clipgenius.sqlite", "app/db/clipgenius.sqlite3"]
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                total_removed += 1
                print(f"Removed {db_file}")
            except Exception as e:
                print(f"Failed to remove {db_file}: {e}")
    
    print("\n" + "=" * 50)
    print(f"Cleanup complete! Removed {total_removed} file(s)/directory(ies)")
    print("=" * 50)

if __name__ == "__main__":
    main()

