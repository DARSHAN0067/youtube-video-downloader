import yt_dlp
import os
from pathlib import Path

# Directory for downloaded files
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

def check_file_type(filepath):
    """Check magic bytes to determine file type."""
    if not filepath.exists():
        print(f"File not found: {filepath}")
        return "MISSING"
        
    with open(filepath, 'rb') as f:
        header = f.read(4)
    
    print(f"File header (hex): {header.hex().upper()}")
    
    if header.startswith(b'ID3') or header.startswith(b'\xFF\xFB') or header.startswith(b'\xFF\xF3') or header.startswith(b'\xFF\xF2'):
        return "MP3"
    elif header.startswith(b'\x00\x00\x00') and (b'ftyp' in f.read(16)):
        return "MP4/M4A"
    else:
        return "UNKNOWN"

def test_download_and_convert():
    url = "https://youtu.be/cmttT32bTcU"
    print(f"Testing download for: {url}")
    
    # Same options as in downloader.py
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'restrictfilenames': True, # We added this earlier
        'windowsfilenames': True,
        'verbose': True, # Enable verbose to see ffmpeg interaction
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # yt-dlp prepare_filename returns the original extension (usually m4a or webm from the format selection)
            # but the file on disk SHOULD be key-changed to mp3 by postprocessor.
            
            print(f"yt-dlp returned filename: {filename}")
            
            # The expected file should be .mp3
            base = os.path.splitext(filename)[0]
            expected_mp3 = base + '.mp3'
            
            print(f"Checking for expected MP3: {expected_mp3}")
            file_type = check_file_type(Path(expected_mp3))
            print(f"Detected File Type: {file_type}")
            
            # Check if original file exists (conversion failure?)
            if file_type == "MISSING":
                print(f"Checking if original file exists: {filename}")
                if Path(filename).exists():
                    print("Original file EXISTS! Conversion failed but no error raised?")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_download_and_convert()
