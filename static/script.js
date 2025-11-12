// Get DOM elements
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatMessages = document.getElementById('chat-messages');
const sendButton = document.getElementById('send-button');
const buttonText = sendButton.querySelector('.button-text');
const loadingSpinner = sendButton.querySelector('.loading-spinner');
const themeToggle = document.getElementById('theme-toggle');
const clearButton = document.getElementById('clear-button');

// Remove welcome message on first message
let isFirstMessage = true;

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

// Handle form submission
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = userInput.value.trim();
    if (!message) return;

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

    // Disable send button
    setButtonLoading(true);

    // Show typing indicator
    const typingIndicator = showTypingIndicator();

    try {
        // Send HTTP request to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        // Remove typing indicator
        hideTypingIndicator(typingIndicator);

        if (response.ok && data.success) {
            // Add AI response
            addMessage(data.response, 'ai');
        } else {
            // Handle error
            showError(data.error || 'An error occurred while processing your request');
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
 */
function addMessage(text, type) {
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

    // For AI messages, parse markdown; for user messages, use plain text
    if (type === 'ai') {
        content.innerHTML = parseMarkdown(text);
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
                <p>I'm an AI agent, ready to answer your questions. Just type your question below!</p>
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
