/**
 * Sidebar Management for Day 11 - Conversation History
 */

// Current active conversation
let currentConversationId = null;

/**
 * Load and render sidebar conversations
 */
async function loadSidebar() {
    const listContainer = document.querySelector('.conversations-list');

    if (!listContainer) {
        console.error('Conversations list container not found');
        return;
    }

    // Show loading state
    showLoadingState(listContainer);

    try {
        const response = await fetch('/api/conversations');
        const data = await response.json();

        if (data.success) {
            renderConversations(data.conversations);
            updateStatsDisplay();
        } else {
            console.error('Failed to load conversations:', data.error);
            showEmptyState(listContainer, 'Failed to load conversations');
        }
    } catch (error) {
        console.error('Error loading sidebar:', error);
        showEmptyState(listContainer, 'Error loading conversations');
    }
}

/**
 * Render conversations grouped by date
 */
function renderConversations(grouped) {
    const listContainer = document.querySelector('.conversations-list');
    listContainer.innerHTML = '';

    const groups = [
        { key: 'today', label: '📅 Today' },
        { key: 'yesterday', label: '📅 Yesterday' },
        { key: 'last_7_days', label: '📅 Last 7 days' },
        { key: 'older', label: '📅 Older' }
    ];

    let hasAnyConversations = false;

    groups.forEach(group => {
        const conversations = grouped[group.key] || [];

        if (conversations.length > 0) {
            hasAnyConversations = true;
            const groupDiv = createDateGroup(group.label, conversations);
            listContainer.appendChild(groupDiv);
        }
    });

    if (!hasAnyConversations) {
        showEmptyState(listContainer, 'No conversations yet');
    }
}

/**
 * Create date group element
 */
function createDateGroup(label, conversations) {
    const groupDiv = document.createElement('div');
    groupDiv.className = 'date-group';

    const header = document.createElement('h3');
    header.textContent = label;
    groupDiv.appendChild(header);

    const conversationsDiv = document.createElement('div');
    conversationsDiv.className = 'conversations';

    conversations.forEach(conv => {
        const item = createConversationItem(conv);
        conversationsDiv.appendChild(item);
    });

    groupDiv.appendChild(conversationsDiv);
    return groupDiv;
}

/**
 * Create conversation item element
 */
function createConversationItem(conv) {
    const div = document.createElement('div');
    div.className = 'conversation-item';
    div.dataset.id = conv.id;

    if (conv.id === currentConversationId) {
        div.classList.add('active');
    }

    div.innerHTML = `
        <div class="conversation-content">
            <div class="conversation-title">${escapeHtml(conv.title)}</div>
            <div class="conversation-time">${conv.time_ago}</div>
        </div>
        <div class="conversation-actions">
            <button class="btn-rename" data-id="${conv.id}" title="Rename">✏️</button>
            <button class="btn-delete" data-id="${conv.id}" title="Delete">🗑️</button>
        </div>
    `;

    // Click to load conversation (but not on action buttons)
    div.addEventListener('click', (e) => {
        if (!e.target.closest('.conversation-actions')) {
            loadConversation(conv.id);
        }
    });

    return div;
}

/**
 * Load specific conversation
 */
async function loadConversation(convId) {
    try {
        const response = await fetch(`/api/conversations/${convId}`);
        const data = await response.json();

        if (data.success) {
            // Clear current messages
            const messagesContainer = document.getElementById('messages');
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
            }

            // Render loaded messages
            data.messages.forEach(msg => {
                if (window.appendMessage) {
                    window.appendMessage(msg.role, msg.content);
                }
            });

            // Update active conversation
            currentConversationId = convId;
            updateActiveConversation(convId);

            console.log(`Loaded conversation ${convId} with ${data.messages.length} messages`);
        } else {
            console.error('Failed to load conversation:', data.error);
            alert('Failed to load conversation');
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
        alert('Error loading conversation');
    }
}

/**
 * Update active conversation visual state
 */
function updateActiveConversation(convId) {
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });

    const activeItem = document.querySelector(`.conversation-item[data-id="${convId}"]`);
    if (activeItem) {
        activeItem.classList.add('active');
    }
}

/**
 * Create new conversation
 */
async function createNewConversation() {
    try {
        const response = await fetch('/api/conversations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            // Clear messages
            const messagesContainer = document.getElementById('messages');
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
            }

            // Update current conversation
            currentConversationId = data.conversation_id;

            // Reload sidebar
            await loadSidebar();

            console.log(`Created new conversation ${data.conversation_id}`);
        } else {
            console.error('Failed to create conversation:', data.error);
            alert('Failed to create new conversation');
        }
    } catch (error) {
        console.error('Error creating conversation:', error);
        alert('Error creating new conversation');
    }
}

/**
 * Rename conversation
 */
async function renameConversation(convId) {
    const currentItem = document.querySelector(`.conversation-item[data-id="${convId}"]`);
    const currentTitle = currentItem?.querySelector('.conversation-title')?.textContent || '';

    const newTitle = prompt('New title:', currentTitle);

    if (newTitle && newTitle.trim()) {
        try {
            const response = await fetch(`/api/conversations/${convId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: newTitle.trim() })
            });

            const data = await response.json();

            if (data.success) {
                await loadSidebar();
                console.log(`Renamed conversation ${convId}`);
            } else {
                console.error('Failed to rename:', data.error);
                alert('Failed to rename conversation');
            }
        } catch (error) {
            console.error('Error renaming conversation:', error);
            alert('Error renaming conversation');
        }
    }
}

/**
 * Delete conversation
 */
async function deleteConversation(convId) {
    if (!confirm('Delete this conversation?')) {
        return;
    }

    try {
        const response = await fetch(`/api/conversations/${convId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            // If deleted active conversation, create new one
            if (convId == currentConversationId) {
                await createNewConversation();
            } else {
                await loadSidebar();
            }

            console.log(`Deleted conversation ${convId}`);
        } else {
            console.error('Failed to delete:', data.error);
            alert('Failed to delete conversation');
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
        alert('Error deleting conversation');
    }
}

/**
 * Update stats display
 */
async function updateStatsDisplay() {
    try {
        const response = await fetch('/api/memory/stats');
        const data = await response.json();

        if (data.success) {
            const totalChatsEl = document.getElementById('total-chats');
            if (totalChatsEl) {
                totalChatsEl.textContent = data.stats.total_conversations;
            }

            const memoryStatusEl = document.getElementById('memory-status');
            if (memoryStatusEl) {
                memoryStatusEl.textContent = 'Active';
                memoryStatusEl.style.color = '#10a37f';
            }
        }
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

/**
 * Clear all memory
 */
async function clearAllMemory() {
    if (!confirm('Clear ALL conversation history? This cannot be undone!')) {
        return;
    }

    try {
        const response = await fetch('/api/memory/clear', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            await createNewConversation();
            alert('All memory cleared');
        } else {
            console.error('Failed to clear memory:', data.error);
            alert('Failed to clear memory');
        }
    } catch (error) {
        console.error('Error clearing memory:', error);
        alert('Error clearing memory');
    }
}

/**
 * Show loading state
 */
function showLoadingState(container) {
    container.innerHTML = `
        <div class="conversations-loading">
            <div class="loading-spinner"></div>
            <p>Loading conversations...</p>
        </div>
    `;
}

/**
 * Show empty state
 */
function showEmptyState(container, message) {
    container.innerHTML = `
        <div class="conversations-empty">
            <p>${message}</p>
        </div>
    `;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Initialize sidebar
 */
function initSidebar() {
    // Load conversations on page load
    loadSidebar();

    // New chat button
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewConversation);
    }

    // Clear all button
    const clearAllBtn = document.getElementById('clear-all-btn');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', clearAllMemory);
    }

    // Event delegation for rename/delete buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-rename')) {
            const convId = parseInt(e.target.dataset.id);
            renameConversation(convId);
        } else if (e.target.classList.contains('btn-delete')) {
            const convId = parseInt(e.target.dataset.id);
            deleteConversation(convId);
        }
    });

    console.log('✅ Sidebar initialized');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSidebar);
} else {
    initSidebar();
}
