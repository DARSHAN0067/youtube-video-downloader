"""
YouTube Video Downloader - Core Download Engine
Uses yt-dlp for reliable video extraction and FFmpeg for merging
"""

import os
import re
import yt_dlp
from typing import Optional, Callable
from pathlib import Path

# Directory for downloaded files
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)


def is_valid_youtube_url(url: str) -> bool:
    """Validate if the URL is a valid YouTube URL."""
    youtube_patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/embed/[\w-]+',
    ]
    return any(re.match(pattern, url) for pattern in youtube_patterns)



def is_valid_playlist_url(url: str) -> bool:
    """Validate if the URL is a valid YouTube Playlist URL."""
    playlist_patterns = [
        r'(https?://)?(www\.)?youtube\.com/playlist\?list=[\w-]+',
    ]
    return any(re.match(pattern, url) for pattern in playlist_patterns)


def get_playlist_info(url: str) -> dict:
    """
    Extract playlist metadata and video list.
    """
    if not is_valid_playlist_url(url):
        raise ValueError("Invalid YouTube Playlist URL")
    
    ydl_opts = {
        'extract_flat': True,  # Don't download, just list
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        entries = []
        if 'entries' in info:
            for entry in info['entries']:
                # Filter out private/deleted videos (usually have no title or duration)
                if entry.get('title') and entry.get('title') != '[Private video]':
                    entries.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'url': entry.get('url'),
                        'duration': entry.get('duration'),
                        'uploader': entry.get('uploader'),
                    })
        
        return {
            'id': info.get('id'),
            'title': info.get('title'),
            'uploader': info.get('uploader'),
            'entry_count': len(entries),
            'entries': entries,
        }


def get_video_info(url: str) -> dict:
    """
    Extract video metadata from YouTube URL.
    
    Returns:
        dict with title, thumbnail, duration, available formats, etc.
    """
    if not is_valid_youtube_url(url):
        raise ValueError("Invalid YouTube URL")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # Extract available qualities
        formats = info.get('formats', [])
        available_qualities = set()
        
        for f in formats:
            height = f.get('height')
            if height and f.get('vcodec') != 'none':
                available_qualities.add(height)
        
        # Sort qualities
        qualities = sorted(available_qualities, reverse=True)
        
        return {
            'id': info.get('id'),
            'title': info.get('title'),
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration'),
            'duration_string': info.get('duration_string'),
            'uploader': info.get('uploader'),
            'view_count': info.get('view_count'),
            'upload_date': info.get('upload_date'),
            'description': info.get('description', '')[:200],
            'available_qualities': qualities,
        }


def download_video(
    url: str,
    quality: str = "best",
    audio_only: bool = False,
    progress_callback: Optional[Callable[[dict], None]] = None
) -> str:
    """
    Download video from YouTube.
    
    Args:
        url: YouTube video URL
        quality: Video quality (360, 480, 720, 1080, 1440, 2160, or 'best')
        audio_only: If True, download audio only as MP3
        progress_callback: Function to call with progress updates
    
    Returns:
        Path to the downloaded file
    """
    if not is_valid_youtube_url(url):
        raise ValueError("Invalid YouTube URL")
    
    # Build format string based on quality selection
    if audio_only:
        format_string = "bestaudio[ext=m4a]/bestaudio/best"
        output_template = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")
        postprocessors = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        if quality == "best":
            format_string = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        else:
            # Try to get specific quality, fallback to best available
            height = quality.replace('p', '')
            format_string = (
                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={height}]+bestaudio/"
                f"best[height<={height}]/best"
            )
        output_template = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")
        postprocessors = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
    
    def progress_hook(d):
        """Handle download progress updates."""
        if progress_callback and d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0:
                percent = (downloaded / total) * 100
            else:
                percent = 0
            
            progress_callback({
                'status': 'downloading',
                'percent': round(percent, 1),
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0),
                'downloaded': downloaded,
                'total': total,
            })
        elif progress_callback and d['status'] == 'finished':
            progress_callback({
                'status': 'processing',
                'percent': 100,
                'message': 'Merging video and audio...'
            })
    
    ydl_opts = {
        'format': format_string,
        'outtmpl': output_template,
        'progress_hooks': [progress_hook],
        'postprocessors': postprocessors,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        # Avoid issues with special characters in filenames
        'restrictfilenames': True,
        'windowsfilenames': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        # Determine the output filename
        if audio_only:
            filename = ydl.prepare_filename(info)
            # Change extension to mp3
            filename = os.path.splitext(filename)[0] + '.mp3'
        else:
            filename = ydl.prepare_filename(info)
            # Change extension to mp4
            filename = os.path.splitext(filename)[0] + '.mp4'
        
        return filename


def get_download_path(filename: str) -> Path:
    """Get the full path for a downloaded file."""
    return DOWNLOAD_DIR / filename


def list_downloads() -> list:
    """List all downloaded files."""
    files = []
    for f in DOWNLOAD_DIR.iterdir():
        if f.is_file() and f.suffix in ['.mp4', '.mp3', '.webm', '.m4a']:
            files.append({
                'name': f.name,
                'size': f.stat().st_size,
                'path': str(f),
            })
    return files


def delete_file(filename: str) -> bool:
    """Delete a downloaded file."""
    filepath = DOWNLOAD_DIR / filename
    if filepath.exists() and filepath.is_file():
        filepath.unlink()
        return True
    return False
