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
const intelligentModeCheckbox = document.getElementById('intelligent-mode-checkbox');
const maxTokensInput = document.getElementById('max-tokens-input');

// Enforce min/max limits on max tokens input
maxTokensInput.addEventListener('change', () => {
    let value = parseInt(maxTokensInput.value);
    if (maxTokensInput.value && (isNaN(value) || value < 1)) {
        maxTokensInput.value = 1;
    } else if (value > 16384) {
        maxTokensInput.value = 16384;
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

// Initialize CSRF token
fetchCsrfToken();

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
    // If all fields are empty, return [null] to use server default
    const values = inputs.map(input => input.value ? parseFloat(input.value) : null);
    // Filter out NaN but keep null
    return values.filter(val => val === null || !isNaN(val));
}

function updateRemoveButtons() {
    const slots = document.querySelectorAll('.temperature-slot');
    slots.forEach((slot, index) => {
        const removeBtn = slot.querySelector('.remove-temp');
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
        const lastTemp = parseFloat(document.querySelector('.temperature-slot:last-child .temp-input').value);
        const newTemp = Math.min(2, lastTemp + 0.3); // Suggest next temperature
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
    if (temperatures.length === 0) {
        alert('Please add at least one temperature value');
        return;
    }

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
        const intelligentMode = intelligentModeCheckbox.checked;

        // Send requests for each temperature in parallel
        const requests = temperatures.map(temp =>
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    message: message,
                    format: selectedFormat,
                    fields: enabledFields,
                    temperature: temp,
                    intelligent_mode: intelligentMode,
                    max_tokens: maxTokensInput.value ? parseInt(maxTokensInput.value) : null
                })
            })
        );

        const responses = await Promise.all(requests);
        const results = await Promise.all(responses.map(r => r.json()));

        // Remove typing indicator
        hideTypingIndicator(typingIndicator);

        // Display comparison results
        displayTemperatureComparison(temperatures, results, selectedFormat);

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
    // Escape HTML to prevent XSS
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

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

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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

    results.forEach((result, index) => {
        const tempResult = document.createElement('div');
        tempResult.className = 'temp-result';

        const header = document.createElement('div');
        header.className = 'temp-result-header';
        // Use temperature from server response if available, otherwise from input
        const tempValue = result.temperature !== undefined ? result.temperature : temperatures[index];
        header.innerHTML = `
            <span class="temp-label">Temperature</span>
            <span class="temp-value">${tempValue}</span>
        `;

        const content = document.createElement('div');
        content.className = 'temp-result-content';

        if (result.error) {
            content.innerHTML = `<div class="parse-error">Error: ${escapeHtml(result.error)}</div>`;
        } else if (result.success) {
            content.innerHTML = renderResponse(result.response, format, result.parsed);
        } else {
            content.innerHTML = '<div class="parse-error">Unknown error occurred</div>';
        }

        // Add token info footer
        const tokenInfo = document.createElement('div');
        tokenInfo.className = 'token-info';

        if (result.tokens) {
            const tokens = result.tokens;
            const percentage = tokens.percentage;
            let colorClass = 'token-green';
            if (percentage > 80) colorClass = 'token-red';
            else if (percentage > 50) colorClass = 'token-yellow';

            tokenInfo.innerHTML = `
                <div class="token-stats">
                    <span class="token-item">In: ${tokens.input}</span>
                    <span class="token-item">Out: ${tokens.output}/${tokens.max_output}</span>
                    <span class="token-item">Total: ${tokens.total}</span>
                </div>
                ${result.truncated ? '<div class="token-warning">Response truncated</div>' : ''}
            `;
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

// Handle Enter key for sending (Shift+Enter for new line not supported in input)
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
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

customFieldsInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' || e.key === ',') {
        e.preventDefault();
        const value = customFieldsInput.value.trim().replace(',', '');

        if (!value) return;

        // Validate field name
        if (value.length > MAX_FIELD_NAME_LENGTH) {
            alert(`Field name too long. Maximum ${MAX_FIELD_NAME_LENGTH} characters.`);
            return;
        }

        if (!isValidFieldName(value)) {
            alert('Invalid field name. Use only letters, numbers, and underscores. Must start with a letter.');
            return;
        }

        if (customFields.includes(value)) {
            alert('Field already exists.');
            return;
        }

        if (customFields.length >= MAX_CUSTOM_FIELDS) {
            alert(`Maximum ${MAX_CUSTOM_FIELDS} custom fields allowed.`);
            return;
        }

        customFields.push(value);
        renderCustomFieldsPreview();
        customFieldsInput.value = '';
    }
});

customFieldsInput.addEventListener('blur', () => {
    const value = customFieldsInput.value.trim().replace(',', '');

    if (!value) return;

    // Validate field name
    if (value.length > MAX_FIELD_NAME_LENGTH) {
        alert(`Field name too long. Maximum ${MAX_FIELD_NAME_LENGTH} characters.`);
        customFieldsInput.value = '';
        return;
    }

    if (!isValidFieldName(value)) {
        alert('Invalid field name. Use only letters, numbers, and underscores. Must start with a letter.');
        customFieldsInput.value = '';
        return;
    }

    if (customFields.includes(value)) {
        customFieldsInput.value = '';
        return;
    }

    if (customFields.length >= MAX_CUSTOM_FIELDS) {
        alert(`Maximum ${MAX_CUSTOM_FIELDS} custom fields allowed.`);
        customFieldsInput.value = '';
        return;
    }

    customFields.push(value);
    renderCustomFieldsPreview();
    customFieldsInput.value = '';
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
