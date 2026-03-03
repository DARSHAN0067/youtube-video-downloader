"""
YouTube Video Downloader - Flask Web Application
A modern web app for downloading YouTube videos with quality selection
"""

from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import threading
import uuid
import time
from downloader import (
    get_video_info,
    get_playlist_info,
    download_video,
    is_valid_youtube_url,
    is_valid_playlist_url,
    DOWNLOAD_DIR
)

app = Flask(__name__)

# Store for tracking download progress
download_tasks = {}


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/info', methods=['POST'])
def video_info():
    """
    Get video metadata from YouTube URL.
    
    Request body: { "url": "https://youtube.com/watch?v=..." }
    """
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    try:
        info = get_video_info(url)
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playlist/info', methods=['POST'])
def playlist_info():
    """
    Get playlist metadata.
    """
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not is_valid_playlist_url(url):
        return jsonify({'error': 'Invalid Playlist URL'}), 400
    
    try:
        info = get_playlist_info(url)
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def start_download():
    """
    Start a video download.
    
    Request body: {
        "url": "https://youtube.com/watch?v=...",
        "quality": "720",
        "audio_only": false
    }
    """
    data = request.get_json()
    url = data.get('url', '')
    quality = data.get('quality', 'best')
    audio_only = data.get('audio_only', False)
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    # Create a task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task status
    download_tasks[task_id] = {
        'status': 'starting',
        'percent': 0,
        'filename': None,
        'error': None,
    }
    
    def download_thread():
        """Run download in background thread."""
        def progress_callback(progress):
            download_tasks[task_id].update(progress)
        
        try:
            filename = download_video(
                url=url,
                quality=quality,
                audio_only=audio_only,
                progress_callback=progress_callback
            )
            filename_str = Path(filename).name
            print(f"Download completed: {filename_str}")
            download_tasks[task_id].update({
                'status': 'completed',
                'percent': 100,
                'filename': filename_str,
            })
        except Exception as e:
            download_tasks[task_id].update({
                'status': 'error',
                'error': str(e),
            })
    
    # Start download in background
    thread = threading.Thread(target=download_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id})


@app.route('/api/progress/<task_id>')
def get_progress(task_id):
    """Get download progress for a task."""
    if task_id not in download_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(download_tasks[task_id])


@app.route('/api/file/<filename>')
def download_file(filename):
    """Serve a downloaded file."""
    filepath = DOWNLOAD_DIR / filename
    
    if not filepath.exists():
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/cleanup/<task_id>', methods=['DELETE'])
def cleanup_task(task_id):
    """Clean up a completed task."""
    if task_id in download_tasks:
        del download_tasks[task_id]
        return jsonify({'success': True})
    return jsonify({'error': 'Task not found'}), 404


if __name__ == '__main__':
    # Ensure download directory exists
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    
    print("=" * 40)
    print("YouTube Video Downloader")
    print("Running at: http://127.0.0.1:5000")
    print("=" * 40)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
3