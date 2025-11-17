// Get DOM elements
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatMessages = document.getElementById('chat-messages');
const sendButton = document.getElementById('send-button');
const buttonText = sendButton.querySelector('.button-text');
const loadingSpinner = sendButton.querySelector('.loading-spinner');
const themeToggle = document.getElementById('theme-toggle');
const clearButton = document.getElementById('clear-button');
const temperatureSlotsContainer = document.getElementById('temperature-slots');
const addTemperatureButton = document.getElementById('add-temperature');

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

function getTemperatureSlots() {
    return Array.from(document.querySelectorAll('.temperature-slot .temp-input'))
        .map(input => parseFloat(input.value))
        .filter(val => !isNaN(val));
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

function createTemperatureSlot(temperature = 0.7) {
    const slot = document.createElement('div');
    slot.className = 'temperature-slot';
    slot.innerHTML = `
        <label>🌡️ Temperature:</label>
        <input type="number" class="temp-input" min="0" max="2" step="0.1" value="${temperature}" required>
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

    // Disable form while processing
    setLoading(true);

    // Remove welcome message on first interaction
    if (isFirstMessage) {
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        isFirstMessage = false;
    }

    // Display user message
    addMessage(message, 'user');

    // Clear input
    userInput.value = '';

    try {
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
                    temperature: temp
                })
            })
        );

        const responses = await Promise.all(requests);
        const results = await Promise.all(responses.map(r => r.json()));

        // Display comparison results
        displayTemperatureComparison(temperatures, results);

    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, something went wrong. Please try again.', 'assistant', true);
    } finally {
        setLoading(false);
    }
});

function displayTemperatureComparison(temperatures, results) {
    const comparisonContainer = document.createElement('div');
    comparisonContainer.className = 'message assistant-message';

    const comparisonGrid = document.createElement('div');
    comparisonGrid.className = 'temperature-comparison';

    results.forEach((result, index) => {
        const tempResult = document.createElement('div');
        tempResult.className = 'temp-result';

        const header = document.createElement('div');
        header.className = 'temp-result-header';
        header.innerHTML = `
            <span class="temp-label">Temperature</span>
            <span class="temp-value">${temperatures[index]}</span>
        `;

        const content = document.createElement('div');
        content.className = 'temp-result-content';

        if (result.error) {
            content.textContent = `Error: ${result.error}`;
            content.style.color = '#ef4444';
        } else {
            content.textContent = result.response;
        }

        tempResult.appendChild(header);
        tempResult.appendChild(content);
        comparisonGrid.appendChild(tempResult);
    });

    comparisonContainer.appendChild(comparisonGrid);
    chatMessages.appendChild(comparisonContainer);
    scrollToBottom();
}

function addMessage(text, sender, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    if (isError) messageDiv.classList.add('error-message');

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function setLoading(loading) {
    sendButton.disabled = loading;
    userInput.disabled = loading;
    addTemperatureButton.disabled = loading;

    document.querySelectorAll('.temp-input').forEach(input => {
        input.disabled = loading;
    });

    if (loading) {
        buttonText.style.display = 'none';
        loadingSpinner.style.display = 'inline';
    } else {
        buttonText.style.display = 'inline';
        loadingSpinner.style.display = 'none';
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function clearConversation() {
    try {
        const response = await fetch('/api/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });

        if (response.ok) {
            chatMessages.innerHTML = `
                <div class="welcome-message">
                    <h2>Welcome! 👋</h2>
                    <p>Compare how AI responds with different temperature settings. Add multiple temperatures to see side-by-side comparisons!</p>
                    <div style="margin-top: 15px; font-size: 14px; opacity: 0.8;">
                        <strong>Try these prompts:</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>"Explain what Python is in 2 sentences" (temps: 0, 0.7, 1.2)</li>
                            <li>"Write a creative product description" (temps: 0.5, 1.0)</li>
                            <li>"List best practices for code reviews" (temp: 0)</li>
                        </ul>
                    </div>
                </div>
            `;
            isFirstMessage = true;
        }
    } catch (error) {
        console.error('Error clearing conversation:', error);
    }
}
