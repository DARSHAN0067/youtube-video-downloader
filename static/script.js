/**
 * YouTube Video Downloader - Frontend JavaScript
 * Handles UI interactions, API calls, and progress tracking
 */

// DOM Elements
const urlInput = document.getElementById('url-input');
const fetchBtn = document.getElementById('fetch-btn');
const videoInfo = document.getElementById('video-info');
const playlistInfo = document.getElementById('playlist-info');
const downloadOptions = document.getElementById('download-options');
const downloadBtn = document.getElementById('download-btn');
const progressSection = document.getElementById('progress-section');
const batchProgressSection = document.getElementById('batch-progress-section');
const completeSection = document.getElementById('complete-section');
const errorSection = document.getElementById('error-section');

// Video info elements
const videoThumbnail = document.getElementById('video-thumbnail');
const videoTitle = document.getElementById('video-title');
const videoUploader = document.getElementById('video-uploader');
const videoDuration = document.getElementById('video-duration');
const videoViews = document.getElementById('video-views');

// Playlist info elements
const playlistTitle = document.getElementById('playlist-title');
const playlistUploader = document.getElementById('playlist-uploader');
const playlistCount = document.getElementById('playlist-count');
const playlistItems = document.getElementById('playlist-items');
const selectAllBtn = document.getElementById('select-all-btn');
const deselectAllBtn = document.getElementById('deselect-all-btn');

// Progress elements
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const progressStatus = document.getElementById('progress-status');

// Batch Progress elements
const batchCount = document.getElementById('batch-count');
const batchProgressFill = document.getElementById('batch-progress-fill');
const batchProgressText = document.getElementById('batch-progress-text');
const batchStatus = document.getElementById('batch-status');
const currentDownloadInfo = document.getElementById('current-download-info');

// Complete elements
const completeFilename = document.getElementById('complete-filename');
const downloadLink = document.getElementById('download-link');
const newDownloadBtn = document.getElementById('new-download-btn');

// Error elements
const errorMessage = document.getElementById('error-message');
const retryBtn = document.getElementById('retry-btn');

// State
let currentTaskId = null;
let selectedQuality = '1080';
let audioOnly = false;
let progressInterval = null;
let isPlaylist = false;
let playlistData = null;
let playlistQueue = [];
let completedDownloads = [];

// Regex
const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|shorts\/|embed\/)|youtu\.be\/)[\w-]+/;
const playlistRegex = /^(https?:\/\/)?(www\.)?youtube\.com\/playlist\?list=[\w-]+/;

/**
 * Initialize event listeners
 */
function init() {
    console.log("Initializing...");

    // URL input events
    if (urlInput) {
        urlInput.addEventListener('input', handleUrlInput);
        urlInput.addEventListener('paste', () => setTimeout(handleUrlInput, 100));
        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') fetchVideoInfo();
        });
    }

    // Buttons
    if (fetchBtn) fetchBtn.addEventListener('click', fetchVideoInfo);
    if (downloadBtn) downloadBtn.addEventListener('click', startDownload);
    if (newDownloadBtn) newDownloadBtn.addEventListener('click', resetUI);
    if (retryBtn) retryBtn.addEventListener('click', resetUI);
    if (selectAllBtn) selectAllBtn.addEventListener('click', () => toggleAllPlaylistItems(true));
    if (deselectAllBtn) deselectAllBtn.addEventListener('click', () => toggleAllPlaylistItems(false));

    // Quality buttons
    document.querySelectorAll('.quality-btn').forEach(btn => {
        btn.addEventListener('click', () => selectQuality(btn));
    });

    // Format toggle
    document.querySelectorAll('.format-btn').forEach(btn => {
        btn.addEventListener('click', () => selectFormat(btn));
    });
}

/**
 * Handle URL input changes
 */
function handleUrlInput() {
    const url = urlInput.value.trim();
    const isVideo = youtubeRegex.test(url);
    const isList = playlistRegex.test(url);
    const isValid = isVideo || isList;

    fetchBtn.disabled = !isValid;

    if (isValid) {
        urlInput.style.borderColor = 'var(--primary)';
    } else if (url.length > 0) {
        urlInput.style.borderColor = 'var(--error)';
    } else {
        urlInput.style.borderColor = 'var(--glass-border)';
    }
}

/**
 * Fetch video or playlist information
 */
async function fetchVideoInfo() {
    const url = urlInput.value.trim();
    const isList = playlistRegex.test(url);
    const isVideo = youtubeRegex.test(url);

    if (!isList && !isVideo) {
        showError('Please enter a valid YouTube URL');
        return;
    }

    setButtonLoading(fetchBtn, true);
    hideAllSections();

    try {
        const endpoint = isList ? '/api/playlist/info' : '/api/info';

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch info');
        }

        if (isList) {
            isPlaylist = true;
            playlistData = data;
            displayPlaylistInfo(data);
        } else {
            isPlaylist = false;
            displayVideoInfo(data);
        }
    } catch (error) {
        showError(error.message);
    } finally {
        setButtonLoading(fetchBtn, false);
    }
}

/**
 * Display video information
 */
function displayVideoInfo(data) {
    videoThumbnail.src = data.thumbnail || '';
    videoTitle.textContent = data.title || 'Unknown Title';
    videoUploader.textContent = data.uploader || 'Unknown Channel';
    videoDuration.textContent = data.duration_string || formatDuration(data.duration);
    videoViews.textContent = formatViews(data.view_count) + ' views';

    updateQualityButtons(data.available_qualities || []);

    videoInfo.classList.remove('hidden');
    downloadOptions.classList.remove('hidden');
}

/**
 * Display playlist information
 */
function displayPlaylistInfo(data) {
    playlistTitle.textContent = data.title || 'Unknown Playlist';
    playlistUploader.textContent = data.uploader || 'Unknown Channel';
    playlistCount.textContent = `${data.entry_count} videos`;

    // Render items
    playlistItems.innerHTML = '';
    data.entries.forEach((entry, index) => {
        const li = document.createElement('li');
        li.className = 'playlist-item';
        li.innerHTML = `
            <div class="playlist-checkbox">
                <input type="checkbox" id="item-${index}" class="item-checkbox" checked data-index="${index}">
            </div>
            <div class="playlist-item-info">
                <span class="playlist-item-title" title="${entry.title}">${index + 1}. ${entry.title}</span>
                <span class="playlist-item-meta">${formatDuration(entry.duration)}</span>
            </div>
        `;
        playlistItems.appendChild(li);
    });

    playlistInfo.classList.remove('hidden');
    downloadOptions.classList.remove('hidden');
}

/**
 * Toggle all playlist items
 */
function toggleAllPlaylistItems(checked) {
    document.querySelectorAll('.item-checkbox').forEach(cb => cb.checked = checked);
}

/**
 * Update quality buttons
 */
function updateQualityButtons(availableQualities) {
    // If playlist, enable all for now (closest match will be used per video)
    if (isPlaylist) {
        document.querySelectorAll('.quality-btn').forEach(btn => {
            btn.classList.remove('disabled');
            btn.disabled = false;
        });
        return;
    }

    const qualityMap = { '2160': 2160, '1440': 1440, '1080': 1080, '720': 720, '480': 480, '360': 360 };
    document.querySelectorAll('.quality-btn').forEach(btn => {
        const quality = parseInt(btn.dataset.quality);
        const isAvailable = availableQualities.some(q => q >= quality);
        btn.classList.toggle('disabled', !isAvailable);
        btn.disabled = !isAvailable;

        if (!isAvailable && btn.classList.contains('active')) {
            btn.classList.remove('active');
            const next = document.querySelector('.quality-btn:not(.disabled)');
            if (next) {
                next.classList.add('active');
                selectedQuality = next.dataset.quality;
            }
        }
    });
}

function selectQuality(btn) {
    if (btn.disabled) return;
    document.querySelectorAll('.quality-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedQuality = btn.dataset.quality;
}

function selectFormat(btn) {
    document.querySelectorAll('.format-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    audioOnly = btn.dataset.format === 'audio';

    const qualityBtns = document.getElementById('quality-buttons');
    qualityBtns.style.opacity = audioOnly ? '0.5' : '1';
    qualityBtns.style.pointerEvents = audioOnly ? 'none' : 'auto';
}

/**
 * Start download (Single or Playlist)
 */
async function startDownload() {
    if (isPlaylist) {
        startPlaylistDownload();
    } else {
        startSingleDownload();
    }
}

/**
 * Start single video download
 */
async function startSingleDownload() {
    const url = urlInput.value.trim();
    setButtonLoading(downloadBtn, true);

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, quality: selectedQuality, audio_only: audioOnly })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);

        currentTaskId = data.task_id;
        showProgressSection();
        startProgressPolling();
    } catch (error) {
        showError(error.message);
        setButtonLoading(downloadBtn, false);
    }
}

/**
 * Start playlist download
 */
async function startPlaylistDownload() {
    const checkboxes = document.querySelectorAll('.item-checkbox:checked');
    if (checkboxes.length === 0) {
        alert('Please select at least one video to download.');
        return;
    }

    // Build queue
    playlistQueue = Array.from(checkboxes).map(cb => {
        const idx = parseInt(cb.dataset.index);
        return playlistData.entries[idx];
    });

    hideAllSections();
    batchProgressSection.classList.remove('hidden');
    completedDownloads = [];

    processPlaylistQueue();
}

/**
 * Process playlist queue
 */
async function processPlaylistQueue() {
    if (playlistQueue.length === 0) {
        // All done
        showComplete("Batch Download Complete!");
        return;
    }

    const currentItem = playlistQueue.shift();
    const totalSelected = document.querySelectorAll('.item-checkbox:checked').length;
    const completedCount = totalSelected - playlistQueue.length - 1;

    // Update batch stats
    batchCount.textContent = `${completedCount} / ${totalSelected}`;
    const totalPercent = (completedCount / totalSelected) * 100;
    batchProgressFill.style.width = `${totalPercent}%`;
    batchProgressText.textContent = `${Math.round(totalPercent)}%`;
    batchStatus.textContent = `Downloading: ${currentItem.title}`;

    // Start individual download
    try {
        currentDownloadInfo.textContent = `Starting ${currentItem.title}...`;

        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: currentItem.url, // Use strict URL from info
                quality: selectedQuality,
                audio_only: audioOnly
            })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error);

        // Poll for this item
        await pollBatchItem(data.task_id, currentItem.title);

        // Success
        completedDownloads.push(data.filename || currentItem.title);

        // Process next
        processPlaylistQueue();

    } catch (error) {
        console.error("Batch item error:", error);
        currentDownloadInfo.textContent = `Failed: ${currentItem.title} (${error.message})`;
        // Continue to next even if fail
        setTimeout(processPlaylistQueue, 2000);
    }
}

/**
 * Poll for batch item
 */
function pollBatchItem(taskId, title) {
    return new Promise((resolve, reject) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`/api/progress/${taskId}`);
                const data = await response.json();

                if (data.status === 'completed') {
                    clearInterval(interval);
                    resolve(data);
                } else if (data.status === 'error') {
                    clearInterval(interval);
                    reject(new Error(data.error));
                } else {
                    // Update current item status text
                    const percent = Math.round(data.percent || 0);
                    currentDownloadInfo.textContent = `${title}: ${percent}%`;
                }
            } catch (e) {
                clearInterval(interval);
                reject(e);
            }
        }, 1000);
    });
}


function showProgressSection() {
    videoInfo.classList.add('hidden');
    playlistInfo.classList.add('hidden');
    downloadOptions.classList.add('hidden');
    progressSection.classList.remove('hidden');
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
    progressStatus.textContent = 'Starting download...';
}

function startProgressPolling() {
    if (progressInterval) clearInterval(progressInterval);
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/progress/${currentTaskId}`);
            const data = await response.json();
            updateProgress(data);
            if (data.status === 'completed') {
                clearInterval(progressInterval);
                showComplete(data.filename);
            } else if (data.status === 'error') {
                clearInterval(progressInterval);
                showError(data.error || 'Download failed');
            }
        } catch (error) {
            clearInterval(progressInterval);
            showError(error.message);
        }
    }, 500);
}

function updateProgress(data) {
    const percent = data.percent || 0;
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `${Math.round(percent)}%`;
    if (data.status === 'processing') {
        progressStatus.textContent = data.message || 'Processing...';
    } else if (data.speed) {
        progressStatus.textContent = `Speed: ${formatBytes(data.speed)}/s • ETA: ${formatTime(data.eta)}`;
    }
}

function showComplete(filename) {
    progressSection.classList.add('hidden');
    batchProgressSection.classList.add('hidden');
    completeSection.classList.remove('hidden');
    completeFilename.textContent = filename;

    // For batch, link might not be useful for single file
    if (isPlaylist) {
        downloadLink.style.display = 'none'; // Hide single download button
        completeFilename.textContent = `All ${completedDownloads.length} files downloaded to 'downloads' folder.`;
    } else {
        downloadLink.style.display = 'inline-flex';
        downloadLink.href = `/api/file/${encodeURIComponent(filename)}`;
        downloadLink.download = filename;
    }
}

function showError(message) {
    hideAllSections();
    errorSection.classList.remove('hidden');
    errorMessage.textContent = message;
    setButtonLoading(downloadBtn, false); // ensure btn reset
}

function hideAllSections() {
    videoInfo.classList.add('hidden');
    playlistInfo.classList.add('hidden');
    downloadOptions.classList.add('hidden');
    progressSection.classList.add('hidden');
    batchProgressSection.classList.add('hidden');
    completeSection.classList.add('hidden');
    errorSection.classList.add('hidden');
}

function resetUI() {
    urlInput.value = '';
    urlInput.style.borderColor = 'var(--glass-border)';
    fetchBtn.disabled = true;
    hideAllSections();
    currentTaskId = null;
    isPlaylist = false;
    playlistData = null;
    if (progressInterval) clearInterval(progressInterval);
}

function setButtonLoading(btn, loading) {
    if (!btn) return;
    btn.classList.toggle('loading', loading);
    btn.disabled = loading;
}

function formatDuration(seconds) {
    if (!seconds) return '0:00';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hrs > 0) return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatViews(count) {
    if (!count) return '0';
    if (count >= 1000000000) return (count / 1000000000).toFixed(1) + 'B';
    if (count >= 1000000) return (count / 1000000).toFixed(1) + 'M';
    if (count >= 1000) return (count / 1000).toFixed(1) + 'K';
    return count.toString();
}

function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    while (bytes >= 1024 && i < units.length - 1) {
        bytes /= 1024;
        i++;
    }
    return bytes.toFixed(1) + ' ' + units[i];
}

function formatTime(seconds) {
    if (!seconds || seconds < 0) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

document.addEventListener('DOMContentLoaded', init);
