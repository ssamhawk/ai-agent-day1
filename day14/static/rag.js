// RAG Comparison JavaScript

// DOM Elements
const themeToggle = document.getElementById('theme-toggle');
const questionInput = document.getElementById('question-input');
const compareBtn = document.getElementById('compare-btn');
const withRagBtn = document.getElementById('with-rag-btn');
const withoutRagBtn = document.getElementById('without-rag-btn');
const resultsGrid = document.getElementById('results-grid');
const optionsToggle = document.getElementById('options-toggle');
const optionsContent = document.getElementById('options-content');

// Options sliders
const topKSlider = document.getElementById('top-k');
const topKValue = document.getElementById('top-k-value');
const minSimSlider = document.getElementById('min-similarity');
const minSimValue = document.getElementById('min-sim-value');
const temperatureSlider = document.getElementById('temperature');
const temperatureValue = document.getElementById('temperature-value');

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

// Initialize slider values
minSimSlider.value = 0.0;
minSimValue.textContent = '0.00';

// Button handlers
compareBtn.addEventListener('click', () => performQuery('compare'));
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

    // Disable buttons
    compareBtn.disabled = true;
    withRagBtn.disabled = true;
    withoutRagBtn.disabled = true;

    // Show loading state
    if (mode === 'compare') {
        showLoadingState('both');
    } else if (mode === 'with_rag') {
        showLoadingState('with_rag');
    } else {
        showLoadingState('without_rag');
    }

    try {
        const response = await fetch('/api/rag/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question,
                mode,
                top_k: topK,
                min_similarity: minSimilarity,
                temperature
            })
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
        withRagBtn.disabled = false;
        withoutRagBtn.disabled = false;
    }
}

// Show loading state
function showLoadingState(mode) {
    if (mode === 'both') {
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

// Display single result
function displaySingleResult(responseData, mode) {
    resultsGrid.classList.add('single-column');
    resultsGrid.innerHTML = buildResponseCard(responseData, mode);
}

// Build response card HTML
function buildResponseCard(responseData, mode) {
    const isWithRag = mode === 'with_rag';
    const icon = isWithRag ? '📚' : '🤖';
    const title = isWithRag ? 'With RAG' : 'Without RAG';
    const badgeClass = isWithRag ? 'badge-with-rag' : 'badge-without-rag';

    let chunksHtml = '';
    if (isWithRag && responseData.chunks_used && responseData.chunks_used.length > 0) {
        chunksHtml = `
            <div class="chunks-section">
                <div class="chunks-header">
                    <div class="chunks-title">📄 Retrieved Chunks (${responseData.chunks_used.length})</div>
                </div>
                <div class="chunks-list">
                    ${responseData.chunks_used.map(chunk => {
                        const similarity = (chunk.similarity * 100).toFixed(1);
                        const similarityClass = chunk.similarity >= 0.85 ? 'similarity-high' :
                                               chunk.similarity >= 0.70 ? 'similarity-medium' : 'similarity-low';
                        return `
                            <div class="chunk-item">
                                <div class="chunk-header">
                                    <div class="chunk-source">${escapeHtml(chunk.source_file)}</div>
                                    <div class="chunk-similarity ${similarityClass}">${similarity}%</div>
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
                <div class="response-text">${escapeHtml(responseData.answer)}</div>
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
