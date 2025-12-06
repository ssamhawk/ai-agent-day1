// Get DOM elements
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatMessages = document.getElementById('chat-messages');
const sendButton = document.getElementById('send-button');
const buttonText = sendButton.querySelector('.button-text');
const loadingSpinner = sendButton.querySelector('.loading-spinner');
const themeToggle = document.getElementById('theme-toggle');
const clearButton = document.getElementById('clear-button');
const responseFormat = document.getElementById('response-format');
const configButton = document.getElementById('config-button');
const configModal = document.getElementById('config-modal');
const modalClose = document.getElementById('modal-close');
const saveConfigButton = document.getElementById('save-config');
const resetConfigButton = document.getElementById('reset-config');
const pipelineModeCheckbox = document.getElementById('pipeline-mode-checkbox');
const intelligentModeCheckbox = document.getElementById('intelligent-mode-checkbox');
const maxTokensInput = document.getElementById('max-tokens-input');
const compressionCheckbox = document.getElementById('compression-checkbox');
const compressionThreshold = document.getElementById('compression-threshold');
const compressionOptions = document.getElementById('compression-options');
const statsButton = document.getElementById('stats-button');
const statsModal = document.getElementById('stats-modal');
const statsClose = document.getElementById('stats-close');
const settingsToggle = document.getElementById('settings-toggle');
const settingsPanel = document.querySelector('.settings-panel');
const settingsClose = document.getElementById('settings-close');

// Settings panel toggle functionality
function toggleSettingsPanel(open) {
    if (open) {
        settingsPanel.classList.add('is-open');
        settingsToggle.classList.add('is-open');
    } else {
        settingsPanel.classList.remove('is-open');
        settingsToggle.classList.remove('is-open');
    }

    // Update ARIA attributes for accessibility
    const isOpen = settingsPanel.classList.contains('is-open');
    settingsPanel.setAttribute('aria-hidden', !isOpen);
    settingsToggle.setAttribute('aria-expanded', isOpen);
}

settingsToggle.addEventListener('click', () => {
    const isCurrentlyOpen = settingsPanel.classList.contains('is-open');
    toggleSettingsPanel(!isCurrentlyOpen);
});

// Close button handler
if (settingsClose) {
    settingsClose.addEventListener('click', () => {
        toggleSettingsPanel(false);
    });
}

// Toggle compression options visibility
function toggleCompressionOptions() {
    if (compressionCheckbox.checked) {
        compressionOptions.classList.remove('hidden');
    } else {
        compressionOptions.classList.add('hidden');
    }
}

// Initialize compression options visibility
toggleCompressionOptions();

// Add event listener for compression checkbox
compressionCheckbox.addEventListener('change', toggleCompressionOptions);

// Enforce min/max limits on max tokens input
maxTokensInput.addEventListener('change', () => {
    let value = parseInt(maxTokensInput.value);
    if (maxTokensInput.value && (isNaN(value) || value < 1)) {
        maxTokensInput.value = 1;
    } else if (value > 16384) {
        maxTokensInput.value = 16384;
    }
});

// Enforce min/max limits on compression threshold input
compressionThreshold.addEventListener('change', () => {
    let value = parseInt(compressionThreshold.value);
    if (compressionThreshold.value && (isNaN(value) || value < 2)) {
        compressionThreshold.value = 2;
    } else if (value > 30) {
        compressionThreshold.value = 30;
    }
});

// Remove welcome message on first message
let isFirstMessage = true;

// CSRF token management
let csrfToken = null;

// Fetch CSRF token on page load
async function fetchCsrfToken() {
    try {
        const response = await fetch('/api/csrf-token');
        const data = await response.json();
        csrfToken = data.csrf_token;
    } catch (error) {
        console.error('Failed to fetch CSRF token:', error);
    }
}

// Clear conversation on page load to prevent old session data
async function clearOnPageLoad() {
    if (!csrfToken) return;

    try {
        await fetch('/api/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
    } catch (error) {
        console.error('Failed to clear on page load:', error);
    }
}

// Initialize: fetch CSRF token then clear session and init WebSocket
fetchCsrfToken().then(() => {
    clearOnPageLoad();
    initMCPWebSocket();
});

// Field name validation
function isValidFieldName(name) {
    // Allow only letters, numbers, and underscores, must start with letter
    return /^[a-zA-Z][a-zA-Z0-9_]*$/.test(name);
}

// Maximum limits
const MAX_CUSTOM_FIELDS = 10;
const MAX_FIELD_NAME_LENGTH = 50;

// Default configuration
const DEFAULT_CONFIG = {
    answer: true,
    category: true,
    key_points: true,
    confidence: false,
    sources: false,
    related_topics: false
};

// Load saved configuration or use default
let currentConfig = JSON.parse(localStorage.getItem('responseConfig')) || {...DEFAULT_CONFIG};
let customFields = JSON.parse(localStorage.getItem('customFields')) || [];

// Dark mode toggle - default to dark theme
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

// Clear conversation button
clearButton.addEventListener('click', async () => {
    if (confirm('Are you sure you want to clear the conversation history?')) {
        await clearConversation();
    }
});

function updateThemeIcon(theme) {
    themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// ===== Temperature Slots Management =====
const temperatureSlotsContainer = document.getElementById('temperature-slots');
const addTemperatureButton = document.getElementById('add-temperature');

function getTemperatureSlots() {
    const inputs = Array.from(document.querySelectorAll('.temperature-slot .temp-input'));
    const values = inputs.map(input => input.value ? parseFloat(input.value) : null).filter(val => val !== null && !isNaN(val));
    // If no valid temperatures, return [0.7] as default
    return values.length > 0 ? values : [0.7];
}

function updateRemoveButtons() {
    const slots = document.querySelectorAll('.temperature-slot');
    slots.forEach((slot, index) => {
        const removeBtn = slot.querySelector('.remove-temp');
        // Check if button exists before accessing style (issue #24 fix)
        if (!removeBtn) return;

        // Show remove button only if there's more than 1 slot
        if (slots.length > 1) {
            removeBtn.style.display = 'inline-block';
        } else {
            removeBtn.style.display = 'none';
        }
    });
}

function createTemperatureSlot(temperature = null) {
    const slot = document.createElement('div');
    slot.className = 'temperature-slot';
    // No label for additional temperature slots
    const valueAttr = temperature !== null ? `value="${temperature}"` : '';
    slot.innerHTML = `
        <input type="number" class="temp-input" min="0" max="2" step="0.1" ${valueAttr} placeholder="0-2">
        <button type="button" class="remove-temp">✕</button>
    `;

    // Add remove functionality
    const removeBtn = slot.querySelector('.remove-temp');
    removeBtn.addEventListener('click', () => {
        if (document.querySelectorAll('.temperature-slot').length > 1) {
            slot.remove();
            updateRemoveButtons();
        }
    });

    return slot;
}

// Add temperature button handler
addTemperatureButton.addEventListener('click', () => {
    const currentSlots = document.querySelectorAll('.temperature-slot').length;
    if (currentSlots < 5) { // Limit to 5 temperature slots
        const lastTempInput = document.querySelector('.temperature-slot:last-child .temp-input');
        // Check if element exists before accessing value (issue #25 fix)
        const lastTemp = lastTempInput ? parseFloat(lastTempInput.value) : 0.7;
        const newTemp = Math.min(2, (isNaN(lastTemp) ? 0.7 : lastTemp) + 0.3); // Suggest next temperature
        const newSlot = createTemperatureSlot(newTemp.toFixed(1));
        temperatureSlotsContainer.appendChild(newSlot);
        updateRemoveButtons();
    } else {
        alert('Maximum 5 temperature comparisons allowed');
    }
});

// Initialize remove buttons state
updateRemoveButtons();

// Handle Enter key - Shift+Enter for new line, Enter to submit
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
    // Shift+Enter will create a new line naturally
});

// Handle form submission
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = userInput.value.trim();
    if (!message) return;

    const temperatures = getTemperatureSlots();

    // Remove welcome message on first message
    if (isFirstMessage) {
        const welcomeMessage = chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        isFirstMessage = false;
    }

    // Add user message
    addMessage(message, 'user');

    // Clear input field
    userInput.value = '';

    // Disable form while processing
    setButtonLoading(true);

    // Show typing indicator
    const typingIndicator = showTypingIndicator();

    try {
        // Get selected format from dropdown
        const selectedFormat = responseFormat.value;
        const enabledFields = selectedFormat !== 'plain' ? getEnabledFields() : null;
        const pipelineMode = pipelineModeCheckbox.checked;
        const intelligentMode = intelligentModeCheckbox.checked;
        const imageGenMode = document.getElementById('image-gen-mode-checkbox').checked;
        const compressionEnabled = compressionCheckbox.checked;
        const threshold = compressionThreshold.value ? parseInt(compressionThreshold.value) : 10;
        const maxTokens = maxTokensInput.value ? parseInt(maxTokensInput.value) : null;

        // Pipeline mode uses different endpoint and logic
        if (pipelineMode) {
            // Pipeline mode: single autonomous execution
            const temperature = temperatures[0]; // Use first temperature for pipeline

            const response = await fetch('/api/pipeline/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    query: message,
                    temperature: temperature
                })
            });

            const result = await response.json();

            // Remove typing indicator
            hideTypingIndicator(typingIndicator);

            // Display pipeline result
            displayPipelineResult(result);
        } else {
            // Normal mode: temperature comparison
            // Send requests for each temperature in parallel
            const requests = temperatures.map(temp => {
                const requestBody = {
                    message: message,
                    format: selectedFormat,
                    fields: enabledFields,
                    temperature: temp,
                    intelligent_mode: intelligentMode,
                    image_gen_mode: imageGenMode,
                    compression_enabled: compressionEnabled,
                    compression_threshold: threshold,
                    keep_recent: 2
                };

                // Add conversation_id if available (from sidebar)
                if (window.currentConversationId) {
                    requestBody.conversation_id = window.currentConversationId;
                }

                // Only add max_tokens if it's a valid number
                if (maxTokens && maxTokens > 0) {
                    requestBody.max_tokens = maxTokens;
                }

                return fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(requestBody)
                });
            });

            const responses = await Promise.all(requests);
            const results = await Promise.all(responses.map(r => r.json()));

            // Remove typing indicator
            hideTypingIndicator(typingIndicator);

            // Display comparison results
            displayTemperatureComparison(temperatures, results, selectedFormat);
        }

    } catch (error) {
        console.error('Error:', error);
        hideTypingIndicator(typingIndicator);
        showError('Failed to connect to the server. Please check your connection.');
    } finally {
        // Re-enable send button
        setButtonLoading(false);
        userInput.focus();
    }
});

/**
 * Parse markdown-like formatting to HTML
 * @param {string} text - Text with markdown formatting
 * @returns {string} HTML string
 */
function parseMarkdown(text) {
    let html = text;

    // Convert [IMAGE_URL]url[/IMAGE_URL] to img tag FIRST
    html = html.replace(/\[IMAGE_URL\]([^\[]+)\[\/IMAGE_URL\]/g, '<img src="$1" alt="Generated Image" style="max-width: 100%; border-radius: 8px; margin: 10px 0;">');

    // Images ![alt](url) - do FIRST before any escaping
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width: 100%; border-radius: 8px; margin: 10px 0;">');

    // Links [text](url) - before escaping
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

    // Now escape remaining HTML (but preserve our img, div and a tags)
    const protectedTags = [];
    html = html.replace(/(<div[^>]*>.*?<\/div>|<img[^>]+>|<a[^>]+>.*?<\/a>)/gis, (match) => {
        const placeholder = `PROTECTED${protectedTags.length}PROTECTED`;
        protectedTags.push(match);
        return placeholder;
    });

    // Escape HTML to prevent XSS
    html = html
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Restore protected tags
    protectedTags.forEach((tag, i) => {
        html = html.replace(`PROTECTED${i}PROTECTED`, tag);
    });

    // Code blocks (```code```) - must be done before inline code
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Inline code (`code`)
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold (**text** or __text__) - must be done before italic
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

    // Italic (*text* or _text_) - simple version
    html = html.replace(/\*([^\*]+?)\*/g, '<em>$1</em>');
    html = html.replace(/_([^_]+?)_/g, '<em>$1</em>');

    // Headers (### Header)
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // Lists - must preserve line structure
    html = html.replace(/^[\*\-] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>');

    // Wrap consecutive <li> in <ul>
    html = html.replace(/(<li>.*?<\/li>\s*)+/g, '<ul>$&</ul>');

    // Line breaks - double newline = paragraph break
    html = html.replace(/\n\n/g, '<br><br>');
    html = html.replace(/\n/g, '<br>');

    return html;
}

/**
 * Add a message to the chat
 * @param {string} text - Message text
 * @param {string} type - Message type ('user' or 'ai')
 * @param {string} format - Response format (for AI messages)
 * @param {object} parsed - Parsed JSON data (for JSON format)
 */
function addMessage(text, type, format = 'plain', parsed = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    // Create message header with label and copy button
    const header = document.createElement('div');
    header.className = 'message-header';

    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = type === 'user' ? 'You' : 'AI Agent';
    header.appendChild(label);

    // Add copy button only for AI messages
    if (type === 'ai') {
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.textContent = 'Copy';
        copyButton.addEventListener('click', () => copyToClipboard(text, copyButton));
        header.appendChild(copyButton);
    }

    const content = document.createElement('div');
    content.className = 'message-content';

    // Render based on type and format
    if (type === 'ai') {
        content.innerHTML = renderResponse(text, format, parsed);
    } else {
        content.textContent = text;
    }

    messageDiv.appendChild(header);
    messageDiv.appendChild(content);
    chatMessages.appendChild(messageDiv);

    // Scroll to latest message
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Render AI response based on format
 * @param {string} text - Raw response text
 * @param {string} format - Response format
 * @param {object} parsed - Parsed JSON data (if applicable)
 * @returns {string} HTML string
 */
function renderResponse(text, format, parsed) {
    // First convert [IMAGE_URL]...[/IMAGE_URL] to actual img tags
    text = text.replace(/\[IMAGE_URL\]([^\[]+)\[\/IMAGE_URL\]/g, function(match, url) {
        return '<img src="' + url + '" alt="Generated Image" style="max-width:100%;border-radius:8px;margin:10px 0;">';
    });

    switch (format) {
        case 'json':
            return renderJSON(text, parsed);
        case 'xml':
            return renderXML(text);
        case 'markdown':
            return parseMarkdown(text);
        case 'plain':
        default:
            return parseMarkdown(text);
    }
}

/**
 * Render JSON response with pretty formatting
 * @param {string} text - Raw JSON text
 * @param {object} parsed - Parsed JSON object
 * @returns {string} HTML string
 */
function renderJSON(text, parsed) {
    if (parsed) {
        // Successfully parsed JSON - render nicely
        let html = '<div class="json-response">';

        // Field icons mapping
        const fieldIcons = {
            answer: '💬',
            category: '🏷️',
            key_points: '✨',
            confidence: '📊',
            sources: '📚',
            related_topics: '🔗'
        };

        // Render each field dynamically
        Object.keys(parsed).forEach(field => {
            const value = parsed[field];
            const icon = fieldIcons[field] || '📌';
            const label = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

            if (Array.isArray(value)) {
                // Render array fields as lists
                if (value.length > 0) {
                    html += `<div class="json-field"><strong>${icon} ${label}:</strong><ul>`;
                    value.forEach(item => {
                        html += `<li>${escapeHtml(item)}</li>`;
                    });
                    html += '</ul></div>';
                }
            } else if (typeof value === 'object' && value !== null) {
                // Render nested objects
                html += `<div class="json-field"><strong>${icon} ${label}:</strong><pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre></div>`;
            } else {
                // Render simple fields
                html += `<div class="json-field"><strong>${icon} ${label}:</strong> ${escapeHtml(value || 'N/A')}</div>`;
            }
        });

        html += '<details class="raw-json"><summary>View Raw JSON</summary><pre><code>' + escapeHtml(JSON.stringify(parsed, null, 2)) + '</code></pre></details>';
        html += '</div>';
        return html;
    } else {
        // Failed to parse - show raw with error
        return '<div class="parse-error">Invalid JSON format</div><pre><code>' + escapeHtml(text) + '</code></pre>';
    }
}

/**
 * Render XML response with pretty formatting
 * @param {string} text - Raw XML text
 * @returns {string} HTML string
 */
function renderXML(text) {
    try {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(text, 'text/xml');

        // Check for parsing errors
        const parserError = xmlDoc.querySelector('parsererror');
        if (parserError) {
            return '<div class="parse-error">⚠️ Invalid XML format</div><pre><code>' + escapeHtml(text) + '</code></pre>';
        }

        // Extract data from XML
        const response = xmlDoc.querySelector('response');
        if (response) {
            let html = '<div class="xml-response">';

            // Field icons mapping
            const fieldIcons = {
                answer: '💬',
                category: '🏷️',
                key_points: '✨',
                confidence: '📊',
                sources: '📚',
                related_topics: '🔗'
            };

            // Process all child nodes dynamically
            Array.from(response.children).forEach(node => {
                const fieldName = node.nodeName;
                const icon = fieldIcons[fieldName] || '📌';
                const label = fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

                // Check if this is a list container (like key_points, sources, etc.)
                if (node.children.length > 0 && (node.querySelector('point') || node.querySelector('source') || node.querySelector('topic'))) {
                    const items = Array.from(node.children).map(child => child.textContent);
                    if (items.length > 0) {
                        html += `<div class="xml-field"><strong>${icon} ${label}:</strong><ul>`;
                        items.forEach(item => {
                            html += `<li>${escapeHtml(item)}</li>`;
                        });
                        html += '</ul></div>';
                    }
                } else {
                    // Simple field
                    const value = node.textContent || 'N/A';
                    html += `<div class="xml-field"><strong>${icon} ${label}:</strong> ${escapeHtml(value)}</div>`;
                }
            });

            html += '<details class="raw-xml"><summary>View Raw XML</summary><pre><code>' + escapeHtml(text) + '</code></pre></details>';
            html += '</div>';
            return html;
        }

        return '<pre><code>' + escapeHtml(text) + '</code></pre>';
    } catch (error) {
        return '<div class="parse-error">Error parsing XML</div><pre><code>' + escapeHtml(text) + '</code></pre>';
    }
}

// escapeHtml moved to utils.js

/**
 * Display temperature comparison results
 * @param {Array} temperatures - Array of temperature values
 * @param {Array} results - Array of API response results
 * @param {string} format - Response format
 */
function displayTemperatureComparison(temperatures, results, format) {
    const comparisonContainer = document.createElement('div');
    comparisonContainer.className = 'message ai-message';

    const comparisonGrid = document.createElement('div');
    comparisonGrid.className = 'temperature-comparison';

    // Only show temperature header when comparing multiple temperatures
    const showTemperature = temperatures.length > 1;

    results.forEach((result, index) => {
        const tempResult = document.createElement('div');
        tempResult.className = 'temp-result';

        const header = document.createElement('div');
        header.className = 'temp-result-header';
        // Use temperature from server response if available, otherwise from input
        const tempValue = result.temperature !== undefined ? result.temperature : temperatures[index];

        // Check if compression is enabled
        if (result.compression_stats && result.compression_stats.summaries_count > 0) {
            if (showTemperature) {
                header.innerHTML = `
                    <span class="temp-label">Compressed</span>
                    <span class="temp-value">T: ${tempValue} (${result.compression_stats.summaries_count} summaries)</span>
                `;
            } else {
                header.innerHTML = `
                    <span class="temp-label">Compressed</span>
                    <span class="temp-value">${result.compression_stats.summaries_count} summaries</span>
                `;
            }
        } else {
            if (showTemperature) {
                header.innerHTML = `
                    <span class="temp-label">Temperature</span>
                    <span class="temp-value">${tempValue}</span>
                `;
            } else {
                // Don't show any header when there's only 1 temperature and no compression
                header.style.display = 'none';
            }
        }

        const content = document.createElement('div');
        content.className = 'temp-result-content';

        if (result.error) {
            content.innerHTML = `<div class="parse-error">Error: ${escapeHtml(result.error)}</div>`;
        } else if (result.success) {
            console.log('Response:', result.response);
            console.log('Has <div>:', result.response && result.response.includes('<div'));
            console.log('Has <img>:', result.response && result.response.includes('<img'));

            // Check if response contains <div><img> HTML (from image generation)
            if (result.response && result.response.includes('<div') && result.response.includes('<img')) {
                console.log('IMAGE GENERATION DETECTED!');
                // Extract the HTML part and text part
                const imgMatch = result.response.match(/(<div[^>]*>.*?<\/div>)/s);
                console.log('Image match:', imgMatch);
                if (imgMatch) {
                    const imageHtml = imgMatch[1];
                    const textPart = result.response.replace(imageHtml, '').trim();
                    console.log('Setting HTML with image');
                    content.innerHTML = renderResponse(textPart, format, result.parsed) + imageHtml;
                } else {
                    content.innerHTML = renderResponse(result.response, format, result.parsed);
                }
            } else {
                content.innerHTML = renderResponse(result.response, format, result.parsed);
            }
        } else {
            content.innerHTML = '<div class="parse-error">Unknown error occurred</div>';
        }

        // Add token info footer
        const tokenInfo = document.createElement('div');
        tokenInfo.className = 'token-info';

        if (result.tokens) {
            const tokens = result.tokens;
            // Build token stats HTML
            let tokenStatsHTML = `
                <div class="token-stats">
                    <span class="token-item">In: ${tokens.input}</span>
                    <span class="token-item">Out: ${tokens.output}/${tokens.max_output}</span>
                    <span class="token-item">Total: ${tokens.total}</span>`;

            // Add savings if available and > 0
            if (tokens.saved_this_request && tokens.saved_this_request > 0) {
                tokenStatsHTML += `
                    <span class="token-item token-saved">Saved: ${tokens.saved_this_request}</span>`;
            }

            tokenStatsHTML += `
                </div>
                ${result.truncated ? '<div class="token-warning">Response truncated</div>' : ''}
            `;

            tokenInfo.innerHTML = tokenStatsHTML;
        }

        tempResult.appendChild(header);
        tempResult.appendChild(content);
        tempResult.appendChild(tokenInfo);
        comparisonGrid.appendChild(tempResult);
    });

    comparisonContainer.appendChild(comparisonGrid);
    chatMessages.appendChild(comparisonContainer);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @param {HTMLElement} button - Copy button element
 */
async function copyToClipboard(text, button) {
    try {
        await navigator.clipboard.writeText(text);
        const originalText = button.textContent;
        button.textContent = '✓ Copied';
        button.classList.add('copied');

        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
        button.textContent = '✗ Failed';
        setTimeout(() => {
            button.textContent = 'Copy';
        }, 2000);
    }
}

/**
 * Show typing indicator
 * @returns {HTMLElement} Typing indicator element
 */
function showTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message';
    messageDiv.id = 'typing-indicator';

    const header = document.createElement('div');
    header.className = 'message-header';

    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = 'AI Agent';
    header.appendChild(label);

    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';

    messageDiv.appendChild(header);
    messageDiv.appendChild(indicator);
    chatMessages.appendChild(messageDiv);

    // Scroll to indicator
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

/**
 * Hide typing indicator
 * @param {HTMLElement} indicator - Typing indicator element
 */
function hideTypingIndicator(indicator) {
    if (indicator && indicator.parentNode) {
        indicator.remove();
    }
}

/**
 * Show error message
 * @param {string} errorText - Error text
 */
function showError(errorText) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = `Error: ${errorText}`;
    chatMessages.appendChild(errorDiv);

    // Scroll to error
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Remove error message after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

/**
 * Set loading state for send button
 * @param {boolean} isLoading - Whether the button is in loading state
 */
function setButtonLoading(isLoading) {
    sendButton.disabled = isLoading;
    userInput.disabled = isLoading;
    addTemperatureButton.disabled = isLoading;
    responseFormat.disabled = isLoading;
    configButton.disabled = isLoading;

    document.querySelectorAll('.temp-input').forEach(input => {
        input.disabled = isLoading;
    });

    document.querySelectorAll('.remove-temp').forEach(btn => {
        btn.disabled = isLoading;
    });

    if (isLoading) {
        buttonText.style.display = 'none';
        loadingSpinner.style.display = 'inline-block';
    } else {
        buttonText.style.display = 'inline-block';
        loadingSpinner.style.display = 'none';
    }
}

// Focus on input field on page load
window.addEventListener('load', () => {
    userInput.focus();
});

/**
 * Clear conversation history
 */
async function clearConversation() {
    try {
        const response = await fetch('/api/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Clear chat messages
            chatMessages.innerHTML = '';

            // Show welcome message again
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'welcome-message';
            welcomeDiv.innerHTML = `
                <h2>Welcome! 👋</h2>
                <p>I'm an AI agent with configurable response formats. Choose a format and ask your question!</p>
            `;
            chatMessages.appendChild(welcomeDiv);

            isFirstMessage = true;
        } else {
            showError(data.error || 'Failed to clear conversation');
        }
    } catch (error) {
        console.error('Error clearing conversation:', error);
        showError('Failed to clear conversation. Please try again.');
    }
}
// Custom fields functionality
const customFieldsInput = document.getElementById('custom-fields-input');
const customFieldsPreview = document.getElementById('custom-fields-preview');

function renderCustomFieldsPreview() {
    customFieldsPreview.innerHTML = '';
    customFields.forEach(field => {
        const tag = document.createElement('span');
        tag.className = 'custom-field-tag';
        tag.innerHTML = `${field} <span class="remove-tag" data-field="${field}">×</span>`;
        customFieldsPreview.appendChild(tag);
    });

    // Add remove handlers
    document.querySelectorAll('.remove-tag').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const field = e.target.dataset.field;
            customFields = customFields.filter(f => f !== field);
            renderCustomFieldsPreview();
        });
    });
}

// Helper function to validate and add custom field
function addCustomField(value) {
    if (!value) return false;

    // Validate field name
    if (value.length > MAX_FIELD_NAME_LENGTH) {
        alert(`Field name too long. Maximum ${MAX_FIELD_NAME_LENGTH} characters.`);
        return false;
    }

    if (!isValidFieldName(value)) {
        alert('Invalid field name. Use only letters, numbers, and underscores. Must start with a letter.');
        return false;
    }

    if (customFields.includes(value)) {
        alert('Field already exists.');
        return false;
    }

    if (customFields.length >= MAX_CUSTOM_FIELDS) {
        alert(`Maximum ${MAX_CUSTOM_FIELDS} custom fields allowed.`);
        return false;
    }

    customFields.push(value);
    renderCustomFieldsPreview();
    return true;
}

customFieldsInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' || e.key === ',') {
        e.preventDefault();
        const value = customFieldsInput.value.trim().replace(',', '');

        if (addCustomField(value)) {
            customFieldsInput.value = '';
        }
    }
});

customFieldsInput.addEventListener('blur', () => {
    const value = customFieldsInput.value.trim().replace(',', '');

    if (addCustomField(value)) {
        customFieldsInput.value = '';
    }
});

// Stats Button Handler
statsButton.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/compression-stats', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            const stats = data.stats;

            // Populate stats modal with REAL stats (including recent messages)
            document.getElementById('stat-total-messages').textContent = stats.total_messages || 0;
            document.getElementById('stat-summaries').textContent = stats.summaries_count || 0;
            document.getElementById('stat-recent').textContent = stats.recent_messages_count || 0;

            // Show real context size vs what it would be without compression
            document.getElementById('stat-original-tokens').textContent = stats.total_without_compression || 0;
            document.getElementById('stat-compressed-tokens').textContent = stats.actual_context_tokens || 0;
            document.getElementById('stat-savings').textContent = stats.real_savings_tokens || 0;

            const savingsPercent = stats.real_savings_percent || 0;
            document.getElementById('stat-percent').textContent = `${savingsPercent}%`;

            // Display summaries if any exist
            const summariesSection = document.getElementById('summaries-section');
            const summariesList = document.getElementById('summaries-list');

            if (stats.summaries && stats.summaries.length > 0) {
                summariesSection.style.display = 'block';
                summariesList.innerHTML = stats.summaries.map((summary, index) => `
                    <div class="summary-card">
                        <div class="summary-header">Summary ${index + 1}</div>
                        <div class="summary-content">${escapeHtml(summary)}</div>
                    </div>
                `).join('');
            } else {
                summariesSection.style.display = 'none';
            }

            statsModal.classList.add('show');
        }
    } catch (error) {
        console.error('Error fetching compression stats:', error);
        showError('Failed to load compression statistics');
    }
});

// Stats Modal Handlers
statsClose.addEventListener('click', () => {
    statsModal.classList.remove('show');
});

statsModal.addEventListener('click', (e) => {
    if (e.target === statsModal) {
        statsModal.classList.remove('show');
    }
});

// Configuration Modal Handlers
configButton.addEventListener('click', () => {
    // Load current config into checkboxes
    Object.keys(currentConfig).forEach(field => {
        const fieldId = field.replace('_', '-');
        const checkbox = document.getElementById(`field-${fieldId}`);
        if (checkbox) {
            checkbox.checked = currentConfig[field];
        }
    });

    // Render custom fields
    renderCustomFieldsPreview();

    configModal.classList.add('show');
});

modalClose.addEventListener('click', () => {
    configModal.classList.remove('show');
});

configModal.addEventListener('click', (e) => {
    if (e.target === configModal) {
        configModal.classList.remove('show');
    }
});

saveConfigButton.addEventListener('click', () => {
    // Save current checkbox states
    const checkboxes = document.querySelectorAll('input[name="field"]');
    checkboxes.forEach(cb => {
        if (!cb.disabled) {
            currentConfig[cb.value] = cb.checked;
        }
    });

    // Save to localStorage
    localStorage.setItem('responseConfig', JSON.stringify(currentConfig));
    localStorage.setItem('customFields', JSON.stringify(customFields));

    // Close modal
    configModal.classList.remove('show');

    // Show success message
    console.log('Configuration saved:', currentConfig, 'Custom fields:', customFields);
});

resetConfigButton.addEventListener('click', () => {
    currentConfig = {...DEFAULT_CONFIG};
    customFields = [];
    localStorage.setItem('responseConfig', JSON.stringify(currentConfig));
    localStorage.setItem('customFields', JSON.stringify(customFields));

    // Update checkboxes
    Object.keys(currentConfig).forEach(field => {
        const fieldId = field.replace('_', '-');
        const checkbox = document.getElementById(`field-${fieldId}`);
        if (checkbox) {
            checkbox.checked = currentConfig[field];
        }
    });

    // Clear custom fields
    renderCustomFieldsPreview();
    customFieldsInput.value = '';
});

// Get enabled fields for API request
function getEnabledFields() {
    const standardFields = Object.keys(currentConfig).filter(key => currentConfig[key]);
    return [...standardFields, ...customFields];
}

// ===== MCP Integration with WebSocket =====

// WebSocket connection for real-time MCP status
let mcpSocket = null;

/**
 * Initialize WebSocket connection for MCP status updates
 */
function initMCPWebSocket() {
    // Initialize Socket.IO connection
    mcpSocket = io({
        transports: ['websocket', 'polling']
    });

    // Connection event handlers
    mcpSocket.on('connect', () => {
        console.log('WebSocket connected for MCP status');
    });

    mcpSocket.on('disconnect', () => {
        console.log('WebSocket disconnected');
        const statusIndicators = document.getElementById('status-indicators');
        if (statusIndicators) {
            statusIndicators.innerHTML = '<span class="loading-dots">Disconnected</span>';
        }
    });

    // Listen for MCP status updates
    mcpSocket.on('mcp_status', handleMCPStatusUpdate);

    // Handle connection errors
    mcpSocket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        const statusIndicators = document.getElementById('status-indicators');
        if (statusIndicators) {
            statusIndicators.innerHTML = '<span class="status-error">Connection Error</span>';
        }
    });
}

/**
 * Handle MCP status update from WebSocket
 * @param {Object} data - Status update data from server
 */
async function handleMCPStatusUpdate(data) {
    const serversList = document.getElementById('servers-list');
    const statusIndicators = document.getElementById('status-indicators');

    try {
        if (data.success && data.status) {
            const status = data.status;

            // Update status indicators in header
            if (statusIndicators && status.connected) {
                const serverChips = status.servers.map(serverName => {
                    const icon = getServerIcon(serverName);
                    const displayName = getServerDisplayName(serverName);
                    const className = `server-chip ${serverName}`;
                    return `<span class="${className}" title="${escapeHtml(serverName)}"><span class="status-dot active"></span><span class="icon">${icon}</span>${displayName}</span>`;
                }).join('');
                statusIndicators.innerHTML = serverChips;
            } else if (statusIndicators) {
                statusIndicators.innerHTML = '<span class="loading-dots">Disconnected</span>';
            }

            // Fetch available tools
            const toolsResponse = await fetch('/api/mcp/tools', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const toolsData = await toolsResponse.json();

            if (toolsResponse.ok && toolsData.success) {
                displayMCPServers(status, toolsData.tools);
            } else {
                displayMCPStatus(status);
            }
        } else {
            serversList.innerHTML = '<p class="error">Failed to load MCP status</p>';
            if (statusIndicators) {
                statusIndicators.innerHTML = '<span class="status-error">Error</span>';
            }
        }
    } catch (error) {
        console.error('Error handling MCP status update:', error);
        serversList.innerHTML = '<p class="error">Error processing MCP status</p>';
        if (statusIndicators) {
            statusIndicators.innerHTML = '<span class="status-error">Error</span>';
        }
    }
}

/**
 * Display MCP status when tools data is unavailable
 */
function displayMCPStatus(status) {
    const serversList = document.getElementById('servers-list');

    if (!status.connected) {
        serversList.innerHTML = '<p class="no-servers">MCP servers not connected</p>';
        return;
    }

    serversList.innerHTML = `
        <div class="mcp-status-info">
            <p><strong>Mode:</strong> ${escapeHtml(status.mode || 'unknown')}</p>
            <p><strong>Servers:</strong> ${status.servers.length}</p>
            <p><strong>Total Tools:</strong> ${status.tools_count || 0}</p>
            ${status.info ? `<p class="info-note">ℹ️ ${escapeHtml(status.info)}</p>` : ''}
        </div>
    `;
}

/**
 * Display MCP servers in the UI
 * @param {Object} status - MCP status object
 * @param {Object} tools - MCP tools object (server_name -> [tools])
 */
function displayMCPServers(status, tools) {
    const serversList = document.getElementById('servers-list');

    if (!status.connected || !status.servers || status.servers.length === 0) {
        serversList.innerHTML = '<p class="no-servers">No MCP servers connected</p>';
        return;
    }

    // Build server badges
    serversList.innerHTML = status.servers.map(serverName => {
        const icon = getServerIcon(serverName);
        const displayName = getServerDisplayName(serverName);
        const className = `server-badge connected ${serverName}`;
        return `<span class="${className}" title="${escapeHtml(serverName)}"><span class="status-dot"></span>${icon} ${displayName}</span>`;
    }).join('');

    // Add mode info if available
    if (status.info) {
        serversList.innerHTML += `
            <div class="mcp-mode-info">
                <p>ℹ️ ${escapeHtml(status.info)}</p>
            </div>
        `;
    }
}

/**
 * Get icon for server type
 * @param {string} serverName - Server name
 * @returns {string} Icon emoji
 */
function getServerIcon(serverName) {
    const icons = {
        'filesystem': '📁',
        'sqlite': '🗄️',
        'brave-search': '🔍',
        'brave_search': '🔍',
        'fetch': '🌐',
        'github': '🐙',
        'slack': '💬',
        'google-drive': '📂'
    };

    return icons[serverName] || '🔌';
}

/**
 * Get display name for server type
 * @param {string} serverName - Server name
 * @returns {string} Display name
 */
function getServerDisplayName(serverName) {
    const names = {
        'filesystem': 'Files',
        'sqlite': 'SQLite',
        'brave-search': 'Brave',
        'brave_search': 'Brave',
        'fetch': 'Fetch',
        'github': 'GitHub',
        'slack': 'Slack',
        'google-drive': 'Drive'
    };

    return names[serverName] || serverName;
}

/**
 * Display pipeline execution result
 * @param {Object} result - Pipeline result from API
 */
function displayPipelineResult(result) {
    if (!result.success) {
        showError(result.error || 'Pipeline execution failed');
        return;
    }

    // Create pipeline result container
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message pipeline-result';

    // Create header
    const header = document.createElement('div');
    header.className = 'message-header';

    const label = document.createElement('div');
    label.className = 'message-label';
    label.innerHTML = '🔗 Pipeline Agent';

    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-button';
    copyBtn.innerHTML = '📋 Copy';
    copyBtn.onclick = () => copyToClipboard(result.answer, copyBtn);

    header.appendChild(label);
    header.appendChild(copyBtn);

    // Create content
    const content = document.createElement('div');
    content.className = 'message-content';

    // Show pipeline steps if available
    if (result.steps && result.steps.length > 0) {
        const stepsDiv = document.createElement('div');
        stepsDiv.className = 'pipeline-steps';
        stepsDiv.style.cssText = 'margin-bottom: 15px; padding: 12px; background: rgba(99, 102, 241, 0.05); border-radius: 6px; border-left: 3px solid #6366f1;';

        let stepsHtml = '<div style="font-weight: 600; margin-bottom: 8px; color: #6366f1;">🔗 Pipeline Execution:</div>';

        result.steps.forEach((step, idx) => {
            const icon = step.success ? '✅' : '❌';
            const cmdType = step.command.type || 'unknown';
            const cmdText = JSON.stringify(step.command.arguments).slice(0, 60);

            // Use sequential numbering (idx+1) instead of internal step number
            stepsHtml += `<div style="margin: 6px 0; padding-left: 10px;">
                ${icon} <strong>Step ${idx + 1}:</strong> ${escapeHtml(cmdType)} - ${escapeHtml(cmdText)}...
            </div>`;
        });

        stepsHtml += `<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(99, 102, 241, 0.2); font-size: 0.9em; opacity: 0.8;">
            📊 Tool Executions: ${result.steps.length} | 🔄 Total Iterations: ${result.total_steps} | 🛠️ Tools: ${result.tools_used.join(', ')}
        </div>`;

        stepsDiv.innerHTML = stepsHtml;
        content.appendChild(stepsDiv);
    }

    // Show final answer
    const answerDiv = document.createElement('div');
    answerDiv.className = 'pipeline-answer';
    answerDiv.innerHTML = parseMarkdown(result.answer);
    content.appendChild(answerDiv);

    // Show errors if any
    if (result.errors && result.errors.length > 0) {
        const errorsDiv = document.createElement('div');
        errorsDiv.className = 'pipeline-errors';
        errorsDiv.style.cssText = 'margin-top: 10px; padding: 10px; background: rgba(239, 68, 68, 0.05); border-radius: 6px; border-left: 3px solid #ef4444;';

        let errorsHtml = '<div style="font-weight: 600; margin-bottom: 6px; color: #ef4444;">⚠️ Errors encountered:</div>';
        result.errors.forEach(err => {
            errorsHtml += `<div style="margin: 4px 0; font-size: 0.9em;">Step ${err.step}: ${escapeHtml(err.error)}</div>`;
        });

        errorsDiv.innerHTML = errorsHtml;
        content.appendChild(errorsDiv);
    }

    messageDiv.appendChild(header);
    messageDiv.appendChild(content);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Expose addMessage as window.appendMessage for sidebar.js compatibility
// Expose addMessage as window.appendMessage for sidebar.js compatibility
window.appendMessage = function(role, content) {
    const type = role === "user" ? "user" : "ai";
    addMessage(content, type);
    
    // Dispatch event for sidebar to reload after AI message
    if (role === "assistant" || role === "ai") {
        console.log('🔔 AI message added event dispatched');
        document.dispatchEvent(new CustomEvent("ai-message-added"));
    }
};