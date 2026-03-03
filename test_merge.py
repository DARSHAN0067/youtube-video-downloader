from downloader import download_video, DOWNLOAD_DIR
import os
import time

def test_video_merge():
    # Use the user's URL or a known 1080p video
    url = "https://youtu.be/cmttT32bTcU" 
    print(f"Testing VIDEO download (should merge) for: {url}")
    
    # Clean previous download
    for f in DOWNLOAD_DIR.glob("*Udisuve*"):
        try:
            os.remove(f)
            print(f"Deleted old file: {f.name}")
        except:
            pass

    try:
        # Request 1080p to force DASH (separate video/audio streams)
        filename = download_video(url, quality="1080", audio_only=False)
        print(f"Download returned: {filename}")
        
        # Check directory contents
        print("\nFiles in download directory:")
        found_files = list(DOWNLOAD_DIR.iterdir())
        for f in found_files:
            print(f" - {f.name} ({f.stat().st_size} bytes)")
            
        # Check if we have multiple files for the same video
        base_name = os.path.splitext(os.path.basename(filename))[0]
        related_files = [f for f in found_files if base_name in f.name]
        
        if len(related_files) > 1:
            print("\nFAILURE: Multiple files found! Merging might have failed.")
        else:
            print("\nSUCCESS: Single file found. Merging likely succeeded.")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_video_merge()
