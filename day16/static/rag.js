// RAG Comparison JavaScript

// State
let selectedFiles = [];
let socket = null;

// DOM Elements - Query
const themeToggle = document.getElementById('theme-toggle');
const questionInput = document.getElementById('question-input');
const compareBtn = document.getElementById('compare-btn');
const compareRerankingBtn = document.getElementById('compare-reranking-btn');
const withRagBtn = document.getElementById('with-rag-btn');
const withoutRagBtn = document.getElementById('without-rag-btn');
const resultsGrid = document.getElementById('results-grid');
const optionsToggle = document.getElementById('options-toggle');
const optionsContent = document.getElementById('options-content');

// DOM Elements - Modal
const manageDocsBtn = document.getElementById('manage-docs-btn');
const docsModal = document.getElementById('docs-modal');
const closeModal = document.getElementById('close-modal');
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const selectedFilesContainer = document.getElementById('selected-files');
const indexBtn = document.getElementById('index-btn');
const clearFilesBtn = document.getElementById('clear-files-btn');
const clearIndexBtn = document.getElementById('clear-index-btn');
const progressSection = document.getElementById('progress-section');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const progressPercent = document.getElementById('progress-percent');
const settingsToggle = document.getElementById('settings-toggle');
const settingsContent = document.getElementById('settings-content');
const statsDetails = document.getElementById('stats-details');

// Options sliders
const topKSlider = document.getElementById('top-k');
const topKValue = document.getElementById('top-k-value');
const minSimSlider = document.getElementById('min-similarity');
const minSimValue = document.getElementById('min-sim-value');
const temperatureSlider = document.getElementById('temperature');
const temperatureValue = document.getElementById('temperature-value');
const chunkSizeSlider = document.getElementById('chunk-size');
const chunkSizeValue = document.getElementById('chunk-size-value');
const overlapSlider = document.getElementById('overlap');
const overlapValue = document.getElementById('overlap-value');

// Reranking controls
const enableRerankingCheckbox = document.getElementById('enable-reranking');
const rerankingOptions = document.getElementById('reranking-options');
const topKRetrieveSlider = document.getElementById('top-k-retrieve');
const topKRetrieveValue = document.getElementById('top-k-retrieve-value');
const topKFinalSlider = document.getElementById('top-k-final');
const topKFinalValue = document.getElementById('top-k-final-value');

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

// Options toggle
optionsToggle.addEventListener('click', () => {
    optionsToggle.classList.toggle('expanded');
    optionsContent.classList.toggle('expanded');
});

// Sliders
topKSlider.addEventListener('input', (e) => {
    topKValue.textContent = e.target.value;
});

minSimSlider.addEventListener('input', (e) => {
    minSimValue.textContent = parseFloat(e.target.value).toFixed(2);
});

temperatureSlider.addEventListener('input', (e) => {
    temperatureValue.textContent = parseFloat(e.target.value).toFixed(1);
});

// Reranking controls
enableRerankingCheckbox.addEventListener('change', (e) => {
    rerankingOptions.style.display = e.target.checked ? 'block' : 'none';
});

topKRetrieveSlider.addEventListener('input', (e) => {
    topKRetrieveValue.textContent = e.target.value;
});

topKFinalSlider.addEventListener('input', (e) => {
    topKFinalValue.textContent = e.target.value;
});

// Initialize slider values
minSimSlider.value = 0.0;
minSimValue.textContent = '0.00';

// Button handlers
compareBtn.addEventListener('click', () => performQuery('compare'));
compareRerankingBtn.addEventListener('click', () => performQuery('compare_reranking'));
withRagBtn.addEventListener('click', () => performQuery('with_rag'));
withoutRagBtn.addEventListener('click', () => performQuery('without_rag'));

// Enter key to submit
questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        performQuery('compare');
    }
});

// Perform query
async function performQuery(mode) {
    const question = questionInput.value.trim();

    if (!question) {
        showNotification('error', 'Please enter a question');
        return;
    }

    const topK = parseInt(topKSlider.value);
    const minSimilarity = parseFloat(minSimSlider.value);
    const temperature = parseFloat(temperatureSlider.value);
    const enableReranking = enableRerankingCheckbox.checked;
    const topKRetrieve = parseInt(topKRetrieveSlider.value);
    const topKFinal = parseInt(topKFinalSlider.value);

    // Disable buttons
    compareBtn.disabled = true;
    compareRerankingBtn.disabled = true;
    withRagBtn.disabled = true;
    withoutRagBtn.disabled = true;

    // Show loading state
    if (mode === 'compare' || mode === 'compare_reranking') {
        showLoadingState('both', mode === 'compare_reranking');
    } else if (mode === 'with_rag') {
        showLoadingState('with_rag');
    } else {
        showLoadingState('without_rag');
    }

    try {
        const requestBody = {
            question,
            mode,
            top_k: topK,
            min_similarity: minSimilarity,
            temperature,
            enable_reranking: enableReranking
        };

        // Add reranking parameters if enabled or if mode is compare_reranking
        if (enableReranking || mode === 'compare_reranking') {
            requestBody.top_k_retrieve = topKRetrieve;
            requestBody.top_k_final = topKFinal;
        }

        const response = await fetch('/api/rag/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const result = await response.json();

        if (response.ok) {
            displayResults(result, mode);
        } else {
            showNotification('error', result.error || 'Query failed');
            resultsGrid.innerHTML = '<div class="empty-state-full"><div class="empty-icon">❌</div><h3>Query Failed</h3><p>' + (result.error || 'Unknown error') + '</p></div>';
        }
    } catch (error) {
        console.error('Query error:', error);
        showNotification('error', 'Query failed');
        resultsGrid.innerHTML = '<div class="empty-state-full"><div class="empty-icon">❌</div><h3>Query Failed</h3><p>Network error</p></div>';
    } finally {
        // Re-enable buttons
        compareBtn.disabled = false;
        compareRerankingBtn.disabled = false;
        withRagBtn.disabled = false;
        withoutRagBtn.disabled = false;
    }
}

// Show loading state
function showLoadingState(mode, isReranking = false) {
    if (mode === 'both') {
        if (isReranking) {
            resultsGrid.innerHTML = `
                <div class="response-card">
                    <div class="loading-state">
                        <div class="loading-spinner">⏳</div>
                        <div class="loading-text">Querying without reranking...</div>
                    </div>
                </div>
                <div class="response-card">
                    <div class="loading-state">
                        <div class="loading-spinner">⏳</div>
                        <div class="loading-text">Querying with reranking...</div>
                    </div>
                </div>
            `;
        } else {
            resultsGrid.innerHTML = `
                <div class="response-card">
                    <div class="loading-state">
                        <div class="loading-spinner">⏳</div>
                        <div class="loading-text">Querying without RAG...</div>
                    </div>
                </div>
                <div class="response-card">
                    <div class="loading-state">
                        <div class="loading-spinner">⏳</div>
                        <div class="loading-text">Querying with RAG...</div>
                    </div>
                </div>
            `;
        }
        resultsGrid.classList.remove('single-column');
    } else {
        resultsGrid.innerHTML = `
            <div class="response-card">
                <div class="loading-state">
                    <div class="loading-spinner">⏳</div>
                    <div class="loading-text">Querying...</div>
                </div>
            </div>
        `;
        resultsGrid.classList.add('single-column');
    }
}

// Display results
function displayResults(data, mode) {
    if (mode === 'compare') {
        displayComparisonResults(data);
    } else if (mode === 'compare_reranking') {
        displayRerankingComparisonResults(data);
    } else if (mode === 'with_rag') {
        displaySingleResult(data.with_rag, 'with_rag');
    } else {
        displaySingleResult(data.without_rag, 'without_rag');
    }
}

// Display comparison results (side-by-side)
function displayComparisonResults(data) {
    resultsGrid.classList.remove('single-column');

    const withoutRagHtml = buildResponseCard(data.without_rag, 'without_rag');
    const withRagHtml = buildResponseCard(data.with_rag, 'with_rag');

    resultsGrid.innerHTML = withoutRagHtml + withRagHtml;
}

// Display reranking comparison results (without vs with reranking)
function displayRerankingComparisonResults(data) {
    resultsGrid.classList.remove('single-column');

    const withoutRerankingHtml = buildResponseCard(data.without_reranking, 'without_reranking');
    const withRerankingHtml = buildResponseCard(data.with_reranking, 'with_reranking');

    resultsGrid.innerHTML = withoutRerankingHtml + withRerankingHtml;
}

// Display single result
function displaySingleResult(responseData, mode) {
    resultsGrid.classList.add('single-column');
    resultsGrid.innerHTML = buildResponseCard(responseData, mode);
}

// Build response card HTML
function buildResponseCard(responseData, mode) {
    const isWithRag = mode === 'with_rag' || mode === 'without_reranking' || mode === 'with_reranking';
    const isWithReranking = mode === 'with_reranking';
    const isWithoutReranking = mode === 'without_reranking';

    let icon, title, badgeClass;

    if (isWithReranking) {
        icon = '🔄';
        title = 'With Reranking';
        badgeClass = 'badge-with-reranking';
    } else if (isWithoutReranking) {
        icon = '📚';
        title = 'Without Reranking';
        badgeClass = 'badge-without-reranking';
    } else if (isWithRag) {
        icon = '📚';
        title = 'With RAG';
        badgeClass = 'badge-with-rag';
    } else {
        icon = '🤖';
        title = 'Without RAG';
        badgeClass = 'badge-without-rag';
    }

    let chunksHtml = '';
    if (isWithRag && responseData.chunks_used && responseData.chunks_used.length > 0) {
        const hasRerankScores = responseData.chunks_used.some(chunk => chunk.rerank_score !== undefined);

        chunksHtml = `
            <div class="chunks-section">
                <div class="chunks-header">
                    <div class="chunks-title">📄 Retrieved Chunks (${responseData.chunks_used.length})</div>
                </div>
                <div class="chunks-list">
                    ${responseData.chunks_used.map((chunk, index) => {
                        const similarity = (chunk.similarity * 100).toFixed(1);
                        const similarityClass = chunk.similarity >= 0.85 ? 'similarity-high' :
                                               chunk.similarity >= 0.70 ? 'similarity-medium' : 'similarity-low';

                        let scoreHtml = `<div class="chunk-similarity ${similarityClass}">${similarity}%</div>`;

                        // Show rerank score if available
                        if (hasRerankScores && chunk.rerank_score !== undefined) {
                            const rerankScore = chunk.rerank_score.toFixed(3);
                            const rankChange = chunk.rank_change || 0;
                            const rankChangeIcon = rankChange > 0 ? '⬆️' : rankChange < 0 ? '⬇️' : '➡️';
                            const rankChangeClass = rankChange > 0 ? 'rank-up' : rankChange < 0 ? 'rank-down' : 'rank-same';

                            scoreHtml = `
                                <div class="chunk-scores">
                                    <div class="chunk-similarity ${similarityClass}" title="Embedding Similarity">Sim: ${similarity}%</div>
                                    <div class="chunk-rerank" title="Rerank Score">Rerank: ${rerankScore}</div>
                                    <div class="chunk-rank-change ${rankChangeClass}" title="Rank Change">${rankChangeIcon} ${rankChange > 0 ? '+' : ''}${rankChange}</div>
                                </div>
                            `;
                        }

                        return `
                            <div class="chunk-item">
                                <div class="chunk-header">
                                    <div class="chunk-source">${escapeHtml(chunk.source_file)}</div>
                                    ${scoreHtml}
                                </div>
                                <div class="chunk-text">${escapeHtml(chunk.text.substring(0, 200))}${chunk.text.length > 200 ? '...' : ''}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    return `
        <div class="response-card">
            <div class="response-header">
                <div class="response-title">
                    <span>${icon}</span>
                    <span>${title}</span>
                </div>
                <div class="response-badge ${badgeClass}">${title}</div>
            </div>
            <div class="response-content">
                <div class="response-text">${enhanceCitationsWithTooltips(escapeHtml(responseData.answer), responseData.citation_map)}</div>
                ${responseData.sources_section ? createCollapsibleSources(responseData.sources_section) : ''}
                <div class="response-metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">🔤 Tokens:</span>
                        <span class="metadata-value">${responseData.tokens_used}</span>
                    </div>
                    ${isWithRag ? `
                        <div class="metadata-item">
                            <span class="metadata-label">📚 Chunks:</span>
                            <span class="metadata-value">${responseData.chunks_used ? responseData.chunks_used.length : 0}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">📁 Files:</span>
                            <span class="metadata-value">${responseData.source_files ? responseData.source_files.length : 0}</span>
                        </div>
                    ` : ''}
                </div>
                ${chunksHtml}
            </div>
        </div>
    `;
}

// Day 16: Create collapsible sources section
function createCollapsibleSources(sourcesText) {
    const id = 'sources-' + Math.random().toString(36).substr(2, 9);
    return `
        <div class="sources-section">
            <div class="sources-header" onclick="toggleSources('${id}')">
                <span class="sources-icon" id="${id}-icon">▶</span>
                <span class="sources-title">📚 SOURCES</span>
                <span class="sources-hint">(click to expand)</span>
            </div>
            <div class="sources-content" id="${id}" style="display: none;">
                <pre>${escapeHtml(sourcesText)}</pre>
            </div>
        </div>
    `;
}

// Day 16: Toggle sources visibility
function toggleSources(id) {
    const content = document.getElementById(id);
    const icon = document.getElementById(id + '-icon');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.textContent = '▼';
    } else {
        content.style.display = 'none';
        icon.textContent = '▶';
    }
}

// Day 16: Enhance citations with tooltips
function enhanceCitationsWithTooltips(htmlText, citationMap) {
    if (!citationMap || typeof citationMap !== 'object') return htmlText;
    if (!htmlText || typeof htmlText !== 'string') return htmlText || '';

    // Replace [1], [2], [3] etc. with tooltip-enabled spans
    return htmlText.replace(/\[(\d+)\]/g, (match, num) => {
        const citation = citationMap[num];
        if (!citation) {
            // Mark invalid citations
            return `<span class="citation-invalid" title="Invalid citation">${escapeHtml(match)}</span>`;
        }

        // Escape EACH component separately to prevent XSS
        const sourceFile = escapeHtml(citation.source_file || 'unknown');
        const chunkIndex = parseInt(citation.chunk_index) || 0;
        const similarity = parseFloat(citation.similarity || 0);
        const preview = escapeHtml((citation.text_preview || '').substring(0, 200));

        const tooltip = `${sourceFile} (chunk ${chunkIndex})
Relevance: ${(similarity * 100).toFixed(1)}%
Preview: "${preview}"`;

        return `<span class="citation-link" data-tooltip="${tooltip}">${escapeHtml(match)}</span>`;
    });
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show notification
function showNotification(type, message) {
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

// ===== DOCUMENT MANAGEMENT & INDEXING =====

// Initialize Socket.IO
function initSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('indexing_progress', (data) => {
        updateIndexingProgress(data);
    });

    socket.on('indexing_complete', (data) => {
        handleIndexingComplete(data);
    });
}

// Modal Management
manageDocsBtn.addEventListener('click', () => {
    docsModal.classList.remove('hidden');
    loadModalStats();
});

closeModal.addEventListener('click', () => {
    docsModal.classList.add('hidden');
});

// Close modal on backdrop click
docsModal.addEventListener('click', (e) => {
    if (e.target === docsModal) {
        docsModal.classList.add('hidden');
    }
});

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
    updateUploadButtons();
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

// Remove file from selection
window.removeFile = function(index) {
    selectedFiles.splice(index, 1);
    renderSelectedFiles();
    updateUploadButtons();
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

// Update upload buttons state
function updateUploadButtons() {
    const hasFiles = selectedFiles.length > 0;
    indexBtn.disabled = !hasFiles;
    clearFilesBtn.disabled = !hasFiles;
}

// Clear selected files
clearFilesBtn.addEventListener('click', () => {
    selectedFiles = [];
    fileInput.value = '';
    renderSelectedFiles();
    updateUploadButtons();
});

// Settings toggles
settingsToggle.addEventListener('click', () => {
    settingsToggle.classList.toggle('expanded');
    settingsContent.classList.toggle('expanded');
});

// Chunk size and overlap sliders
chunkSizeSlider.addEventListener('input', (e) => {
    chunkSizeValue.textContent = e.target.value;
});

overlapSlider.addEventListener('input', (e) => {
    overlapValue.textContent = e.target.value;
});

// Index documents
indexBtn.addEventListener('click', async () => {
    if (selectedFiles.length === 0) return;

    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files[]', file);
    });

    // Add chunk settings
    const chunkSize = parseInt(chunkSizeSlider.value);
    const overlap = parseInt(overlapSlider.value);
    formData.append('chunk_size', chunkSize);
    formData.append('overlap', overlap);

    // Show progress
    progressSection.classList.remove('hidden');
    indexBtn.disabled = true;
    clearFilesBtn.disabled = true;

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
            updateUploadButtons();
            // Refresh stats
            loadHeaderStats();
            loadModalStats();
        } else {
            showNotification('error', result.error || 'Failed to index documents');
        }
    } catch (error) {
        console.error('Error indexing documents:', error);
        showNotification('error', 'Failed to index documents');
    } finally {
        progressSection.classList.add('hidden');
        indexBtn.disabled = false;
        clearFilesBtn.disabled = false;
    }
});

// Update indexing progress
function updateIndexingProgress(data) {
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
    loadHeaderStats();
    loadModalStats();
}

// Load header statistics
async function loadHeaderStats() {
    try {
        const response = await fetch('/api/indexing/stats');
        const stats = await response.json();

        document.getElementById('header-files').textContent = stats.total_files;
        document.getElementById('header-chunks').textContent = stats.total_chunks;
        document.getElementById('header-tokens').textContent = stats.total_tokens.toLocaleString();
    } catch (error) {
        console.error('Error loading header statistics:', error);
    }
}

// Load modal statistics (indexed files list)
async function loadModalStats() {
    try {
        const response = await fetch('/api/indexing/stats');
        const stats = await response.json();

        // Display file details in modal
        if (stats.files && stats.files.length > 0) {
            statsDetails.innerHTML = stats.files.map(file => `
                <div class="stats-file">
                    <div class="stats-file-name">${getFileIcon(file.name)} ${file.name}</div>
                    <div class="stats-file-info">${file.chunks} chunks • ${file.tokens.toLocaleString()} tokens</div>
                </div>
            `).join('');
        } else {
            statsDetails.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 16px;">No indexed files</div>';
        }
    } catch (error) {
        console.error('Error loading modal statistics:', error);
    }
}

// Clear entire index
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
            loadHeaderStats();
            loadModalStats();
        } else {
            showNotification('error', 'Failed to clear index');
        }
    } catch (error) {
        console.error('Error clearing index:', error);
        showNotification('error', 'Failed to clear index');
    }
});

// Initialize on page load
initSocket();
loadHeaderStats();
updateUploadButtons();
