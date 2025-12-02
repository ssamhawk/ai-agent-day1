/**
 * Sidebar Management for Day 11 - Conversation History
 * Matches existing app design and functionality
 */

// Current active conversation - expose globally for script.js
window.currentConversationId = null;
let currentConversationId = null;
let sidebarHidden = false;

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
        showEmptyState(listContainer, 'No conversations yet. Start chatting!');
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
            // Clear current messages completely
            const messagesContainer = document.getElementById('chat-messages');
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
            }

            // Render loaded messages
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    if (window.appendMessage) {
                        window.appendMessage(msg.role, msg.content);
                    }
                });
            }

            // Update active conversation
            currentConversationId = convId;
            window.currentConversationId = convId;
            updateActiveConversation(convId);

            // Save to localStorage for page refresh persistence
            try {
                localStorage.setItem('currentConversationId', convId);
            } catch (e) {
                console.warn('Could not save conversation ID:', e);
            }

            console.log(`Loaded conversation ${convId} with ${data.messages.length} messages`);
        } else {
            console.error('Failed to load conversation:', data.error);
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
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
        const messagesContainer = document.getElementById('chat-messages');

        // Create new conversation on backend
        const response = await fetch('/api/conversations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });

        const data = await response.json();

        if (data.success) {
            // Clear messages - keep only welcome message
            if (messagesContainer) {
                // Find and keep welcome message, remove others
                const welcomeMsg = messagesContainer.querySelector('.welcome-message');
                messagesContainer.innerHTML = '';
                if (welcomeMsg) {
                    messagesContainer.appendChild(welcomeMsg);
                }
            }

            // Update current conversation ID to new one
            currentConversationId = data.conversation_id;
            window.currentConversationId = data.conversation_id;

            // Save to localStorage for page refresh persistence
            try {
                localStorage.setItem('currentConversationId', data.conversation_id);
            } catch (e) {
                console.warn('Could not save conversation ID:', e);
            }

            // Reload sidebar to show new empty conversation
            await loadSidebar();

            console.log(`Created new conversation ${data.conversation_id}`);
        } else {
            console.error('Failed to create conversation:', data.error);
        }
    } catch (error) {
        console.error('Error creating conversation:', error);
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
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ title: newTitle.trim() })
            });

            const data = await response.json();

            if (data.success) {
                await loadSidebar();
                console.log(`Renamed conversation ${convId}`);
            } else {
                console.error('Failed to rename:', data.error);
            }
        } catch (error) {
            console.error('Error renaming conversation:', error);
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
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        const data = await response.json();

        if (data.success) {
            // If deleted active conversation, create new one
            if (convId == currentConversationId) {
                // Clear localStorage since active conversation is deleted
                try {
                    localStorage.removeItem('currentConversationId');
                } catch (e) {
                    console.warn('Could not clear conversation ID:', e);
                }
                await createNewConversation();
            } else {
                await loadSidebar();
            }

            console.log(`Deleted conversation ${convId}`);
        } else {
            console.error('Failed to delete:', data.error);
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
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
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });

        const data = await response.json();

        if (data.success) {
            // Clear localStorage
            try {
                localStorage.removeItem('currentConversationId');
            } catch (e) {
                console.warn('Could not clear conversation ID:', e);
            }
            await createNewConversation();
            console.log('All memory cleared');
        } else {
            console.error('Failed to clear memory:', data.error);
        }
    } catch (error) {
        console.error('Error clearing memory:', error);
    }
}

/**
 * Toggle sidebar visibility
 */
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');

    if (sidebar) {
        sidebarHidden = !sidebarHidden;

        if (sidebarHidden) {
            sidebar.classList.add('hidden');
            if (toggleBtn) {
                toggleBtn.textContent = '▶';
            }
        } else {
            sidebar.classList.remove('hidden');
            if (toggleBtn) {
                toggleBtn.textContent = '◀';
            }
        }

        // Save preference
        try {
            localStorage.setItem('sidebarHidden', sidebarHidden);
        } catch (e) {
            console.warn('Could not save sidebar state:', e);
        }
    }
}

/**
 * Restore sidebar state from localStorage
 */
function restoreSidebarState() {
    try {
        // Don't restore hidden state - always show sidebar by default
        // User can hide it manually if needed
        const sidebar = document.querySelector('.sidebar');
        const toggleBtn = document.querySelector('.sidebar-toggle');

        if (sidebar) {
            sidebar.classList.remove('hidden');
        }
        if (toggleBtn) {
            toggleBtn.textContent = '◀';
        }
        sidebarHidden = false;
    } catch (e) {
        console.warn('Could not restore sidebar state:', e);
    }
}

/**
 * Get CSRF token
 */
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
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
            <p>${escapeHtml(message)}</p>
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
 * Auto-create conversation when sending first message
 */
function ensureActiveConversation() {
    if (!currentConversationId) {
        // Create conversation silently
        createNewConversation();
    }
}

/**
 * Hook into send message to auto-create conversation
 */
function hookSendMessage() {
    // Don't hook - let conversation be created automatically by backend
    // The backend will create conversation when saving first message
    console.log('Sidebar: Not hooking send message - conversation auto-created by backend');
}

/**
 * Restore conversation from localStorage on page load
 */
async function restoreConversation() {
    try {
        const savedConvId = localStorage.getItem('currentConversationId');

        if (savedConvId) {
            const convId = parseInt(savedConvId);
            console.log(`🔄 Restoring conversation ${convId} from localStorage`);

            // Verify conversation exists in database
            const response = await fetch(`/api/conversations/${convId}`);
            const data = await response.json();

            if (data.success && data.messages) {
                // Load the saved conversation
                await loadConversation(convId);
                console.log(`✅ Restored conversation ${convId}`);
            } else {
                // Conversation doesn't exist anymore, clear localStorage
                console.log(`⚠️ Conversation ${convId} not found, clearing localStorage`);
                localStorage.removeItem('currentConversationId');
            }
        }
    } catch (error) {
        console.error('Error restoring conversation:', error);
        localStorage.removeItem('currentConversationId');
    }
}

/**
 * Initialize sidebar
 */
function initSidebar() {
    // Restore sidebar state
    restoreSidebarState();

    // Load conversations on page load
    loadSidebar();

    // Restore last active conversation from localStorage
    restoreConversation();

    // Hook into message sending
    hookSendMessage();

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

    // Sidebar toggle button
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    // Event delegation for rename/delete buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-rename')) {
            e.stopPropagation();
            const convId = parseInt(e.target.dataset.id);
            renameConversation(convId);
        } else if (e.target.classList.contains('btn-delete')) {
            e.stopPropagation();
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

// Auto-reload sidebar when AI responds (this creates/updates conversation)
document.addEventListener('ai-message-added', function() {
    console.log('📨 Sidebar received ai-message-added event');
    // Reload sidebar after AI response - conversation is created on backend
    // Wait 2 seconds to ensure title generation has completed (happens at 6 messages)
    console.log('⏰ Scheduling sidebar reload in 2 seconds...');
    setTimeout(() => {
        console.log('🔄 Sidebar reload triggered');
        loadSidebar();
    }, 2000);
});
