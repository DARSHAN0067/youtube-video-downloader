import yt_dlp
import os
from pathlib import Path

# Directory for downloaded files
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

def test_generic_download():
    # A generic MP4 link (using a sample video)
    url = "https://filesamples.com/samples/video/mp4/sample_640x360.mp4"
    print(f"Testing download for generic MP4: {url}")
    
    ydl_opts = {
        'format': 'bestaudio/best', # For generic files, we might just want to download best and convert
        'outtmpl': str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'restrictfilenames': True,
        'windowsfilenames': True,
        'verbose': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Extracting info...")
            # Validate if yt-dlp supports it
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            print(f"Original Filename: {filename}")
            
            # expected
            final_name = os.path.splitext(filename)[0] + '.mp3'
            print(f"Expected MP3: {final_name}")
            
            if Path(final_name).exists():
                print("SUCCESS: Generic MP4 converted to MP3!")
            else:
                print("FAILURE: MP3 not found.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_generic_download()
