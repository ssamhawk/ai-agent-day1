// Document Indexing JavaScript

// State
let selectedFiles = [];
let socket = null;

// DOM Elements
const themeToggle = document.getElementById('theme-toggle');
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const selectedFilesContainer = document.getElementById('selected-files');
const indexBtn = document.getElementById('index-btn');
const clearFilesBtn = document.getElementById('clear-files-btn');
const clearIndexBtn = document.getElementById('clear-index-btn');
const searchBtn = document.getElementById('search-btn');
const searchInput = document.getElementById('search-input');
const resultsContainer = document.getElementById('results-container');
const resultsHeader = document.getElementById('results-header');
const progressSection = document.getElementById('progress-section');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const progressPercent = document.getElementById('progress-percent');

// Settings elements
const settingsToggle = document.getElementById('settings-toggle');
const settingsContent = document.getElementById('settings-content');
const searchOptionsToggle = document.getElementById('search-options-toggle');
const searchOptionsContent = document.getElementById('search-options-content');
const chunkSizeSlider = document.getElementById('chunk-size');
const chunkSizeValue = document.getElementById('chunk-size-value');
const overlapSlider = document.getElementById('overlap');
const overlapValue = document.getElementById('overlap-value');
const topKSlider = document.getElementById('top-k');
const topKValue = document.getElementById('top-k-value');
const minSimSlider = document.getElementById('min-similarity');
const minSimValue = document.getElementById('min-sim-value');

// Initialize Socket.IO
function initSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('indexing_progress', (data) => {
        updateProgress(data);
    });

    socket.on('indexing_complete', (data) => {
        handleIndexingComplete(data);
    });
}

// Upload Zone Events
uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragging');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragging');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragging');
    handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

// Handle file selection
function handleFiles(files) {
    const newFiles = Array.from(files).filter(file => {
        // Check if already selected
        if (selectedFiles.find(f => f.name === file.name)) {
            return false;
        }
        // Check file type
        const validTypes = ['md', 'txt', 'py', 'js', 'json', 'csv'];
        const ext = file.name.split('.').pop().toLowerCase();
        return validTypes.includes(ext);
    });

    selectedFiles.push(...newFiles);
    renderSelectedFiles();
    updateButtons();
}

// Render selected files
function renderSelectedFiles() {
    if (selectedFiles.length === 0) {
        selectedFilesContainer.innerHTML = '';
        return;
    }

    selectedFilesContainer.innerHTML = selectedFiles.map((file, index) => {
        const icon = getFileIcon(file.name);
        const size = formatFileSize(file.size);

        return `
            <div class="file-item">
                <div class="file-info">
                    <span class="file-icon">${icon}</span>
                    <span class="file-name">${file.name}</span>
                    <span class="file-size">${size}</span>
                </div>
                <button class="file-remove" onclick="removeFile(${index})">✕</button>
            </div>
        `;
    }).join('');
}

// Remove file
function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderSelectedFiles();
    updateButtons();
}

// Get file icon
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'md': '📄',
        'txt': '📝',
        'py': '🐍',
        'js': '📜',
        'json': '📋',
        'csv': '📊'
    };
    return icons[ext] || '📄';
}

// Format file size
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// Update buttons state
function updateButtons() {
    const hasFiles = selectedFiles.length > 0;
    indexBtn.disabled = !hasFiles;
    clearFilesBtn.disabled = !hasFiles;
}

// Clear files
clearFilesBtn.addEventListener('click', () => {
    selectedFiles = [];
    fileInput.value = '';
    renderSelectedFiles();
    updateButtons();
});

// Index documents
indexBtn.addEventListener('click', async () => {
    if (selectedFiles.length === 0) return;

    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files[]', file);
    });

    // Show progress
    progressSection.classList.remove('hidden');
    indexBtn.disabled = true;

    try {
        const response = await fetch('/api/indexing/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showNotification('success', `Indexed ${result.total_chunks} chunks from ${result.processed.length} files`);
            // Clear selected files
            selectedFiles = [];
            fileInput.value = '';
            renderSelectedFiles();
            updateButtons();
            // Refresh stats
            loadStatistics();
        } else {
            showNotification('error', result.error || 'Failed to index documents');
        }
    } catch (error) {
        console.error('Error indexing documents:', error);
        showNotification('error', 'Failed to index documents');
    } finally {
        progressSection.classList.add('hidden');
        indexBtn.disabled = false;
    }
});

// Update progress
function updateProgress(data) {
    const percent = Math.round(data.progress);
    progressFill.style.width = percent + '%';
    progressPercent.textContent = percent + '%';

    if (data.step === 'reading') {
        progressText.textContent = `Reading ${data.filename}...`;
    } else if (data.step === 'embedding') {
        progressText.textContent = `Generating embeddings for ${data.filename} (${data.chunks} chunks)...`;
    } else if (data.step === 'complete') {
        progressText.textContent = `Completed ${data.filename} (${data.chunks} chunks)`;
    }
}

// Handle indexing complete
function handleIndexingComplete(data) {
    progressSection.classList.add('hidden');
    loadStatistics();
}

// Search
searchBtn.addEventListener('click', performSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});

async function performSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    const topK = parseInt(topKSlider.value);
    const minSimilarity = parseFloat(minSimSlider.value);
    const fileType = document.getElementById('file-type-filter').value;

    searchBtn.disabled = true;
    resultsContainer.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><p>Searching...</p></div>';

    try {
        const response = await fetch('/api/indexing/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query,
                top_k: topK,
                min_similarity: minSimilarity,
                file_type: fileType || null
            })
        });

        const result = await response.json();

        if (response.ok) {
            displayResults(result);
        } else {
            showNotification('error', result.error || 'Search failed');
            resultsContainer.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><p>Search failed</p></div>';
        }
    } catch (error) {
        console.error('Search error:', error);
        showNotification('error', 'Search failed');
        resultsContainer.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><p>Search failed</p></div>';
    } finally {
        searchBtn.disabled = false;
    }
}

// Display search results
function displayResults(data) {
    if (data.results.length === 0) {
        resultsContainer.innerHTML = '<div class="empty-state"><div class="empty-icon">🔍</div><p>No results found</p></div>';
        resultsHeader.innerHTML = '<h3>Search Results</h3>';
        return;
    }

    resultsHeader.innerHTML = `<h3>Search Results (${data.results.length} found)</h3>`;

    resultsContainer.innerHTML = data.results.map((result, index) => {
        const similarity = (result.similarity * 100).toFixed(1);
        const similarityClass = result.similarity >= 0.85 ? 'similarity-high' :
                               result.similarity >= 0.70 ? 'similarity-medium' : 'similarity-low';
        const icon = getFileIcon(result.source_file);

        return `
            <div class="result-item">
                <div class="result-header">
                    <div class="result-title">
                        <span class="result-icon">${icon}</span>
                        <div>
                            <div class="result-filename">${result.source_file}</div>
                            <div class="result-meta">Chunk ${result.chunk_index + 1} • ${result.token_count} tokens</div>
                        </div>
                    </div>
                    <div class="result-similarity ${similarityClass}">
                        ${similarity}%
                    </div>
                </div>
                <div class="result-text">${escapeHtml(result.text)}</div>
                <div class="result-actions">
                    <button class="btn-text" onclick="copyText(\`${escapeHtml(result.text).replace(/`/g, '\\`')}\`)">📋 Copy</button>
                </div>
            </div>
        `;
    }).join('');
}

// Copy text to clipboard
function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('success', 'Copied to clipboard');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showNotification('error', 'Failed to copy');
    });
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch('/api/indexing/stats');
        const stats = await response.json();

        document.getElementById('stat-files').textContent = stats.total_files;
        document.getElementById('stat-chunks').textContent = stats.total_chunks;
        document.getElementById('stat-tokens').textContent = stats.total_tokens.toLocaleString();

        // Display file details
        const detailsContainer = document.getElementById('stats-details');
        if (stats.files && stats.files.length > 0) {
            detailsContainer.innerHTML = stats.files.map(file => `
                <div class="stats-file">
                    <div class="stats-file-name">${getFileIcon(file.name)} ${file.name}</div>
                    <div class="stats-file-info">${file.chunks} chunks • ${file.tokens.toLocaleString()} tokens</div>
                </div>
            `).join('');
        } else {
            detailsContainer.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 16px;">No indexed files</div>';
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Clear index
clearIndexBtn.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear the entire index?')) {
        return;
    }

    try {
        const response = await fetch('/api/indexing/clear', {
            method: 'POST'
        });

        if (response.ok) {
            showNotification('success', 'Index cleared');
            loadStatistics();
            resultsContainer.innerHTML = '<div class="empty-state"><div class="empty-icon">🔍</div><p>Enter a search query to find relevant documents</p></div>';
        } else {
            showNotification('error', 'Failed to clear index');
        }
    } catch (error) {
        console.error('Error clearing index:', error);
        showNotification('error', 'Failed to clear index');
    }
});

// Settings toggles
settingsToggle.addEventListener('click', () => {
    settingsToggle.classList.toggle('expanded');
    settingsContent.classList.toggle('expanded');
});

searchOptionsToggle.addEventListener('click', () => {
    searchOptionsToggle.classList.toggle('expanded');
    searchOptionsContent.classList.toggle('expanded');
});

// Sliders
chunkSizeSlider.addEventListener('input', (e) => {
    chunkSizeValue.textContent = e.target.value;
});

overlapSlider.addEventListener('input', (e) => {
    overlapValue.textContent = e.target.value;
});

topKSlider.addEventListener('input', (e) => {
    topKValue.textContent = e.target.value;
});

minSimSlider.addEventListener('input', (e) => {
    minSimValue.textContent = parseFloat(e.target.value).toFixed(2);
});

// Show notification
function showNotification(type, message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#10B981' : '#EF4444'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Theme toggle
const savedTheme = localStorage.getItem('theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);
updateThemeIcon(savedTheme);

themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
});

function updateThemeIcon(theme) {
    themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// Initialize slider values
minSimSlider.value = 0.0;
minSimValue.textContent = '0.00';

// Initialize
initSocket();
loadStatistics();
updateButtons();
