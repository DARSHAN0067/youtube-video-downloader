import yt_dlp
import json

def test_playlist_extraction():
    # YouTube standard "Music" generated channel playlist or similar
    # Using "Python" topic channel generic link, or a direct video list
    playlist_url = "https://www.youtube.com/playlist?list=PLBf0hpJ_U1RZ9O_H9QZtF5T85M5E3tYfU" # Specific known playlist
    
    print(f"Testing playlist extraction for: {playlist_url}")
    
    ydl_opts = {
        'extract_flat': True, # We just want list of videos, not full details for every single one immediately
        'quiet': True,
        'dump_single_json': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(playlist_url, download=False)
            
            if 'entries' in result:
                print(f"Found playlist: {result.get('title')}")
                print(f"Entry count: {len(result['entries'])}")
                
                # Print first few entries
                for i, entry in enumerate(result['entries'][:3]):
                    print(f"[{i}] {entry.get('title')} (ID: {entry.get('id')})")
                    print(f"    URL: {entry.get('url')}")
                    print(f"    Duration: {entry.get('duration')}")
            else:
                print("Not a playlist or no entries found.")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_playlist_extraction()
