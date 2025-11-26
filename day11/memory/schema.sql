-- Day 11 - External Memory Schema
-- Simplified SQLite schema for single-user home project

-- ============================================
-- CONVERSATIONS TABLE
-- Stores conversation sessions with metadata
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    title TEXT,
    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
    last_updated TIMESTAMP DEFAULT (datetime('now', 'localtime')),
    total_messages INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    is_archived BOOLEAN DEFAULT 0,
    metadata TEXT  -- JSON: {model, temperature, language, etc}
);

-- ============================================
-- MESSAGES TABLE
-- Stores all conversation messages
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
    token_count INTEGER DEFAULT 0,
    metadata TEXT,  -- JSON: {format, temperature, etc}

    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- ============================================
-- SUMMARIES TABLE
-- Stores compression summaries
-- ============================================
CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    summary_text TEXT NOT NULL,
    messages_compressed INTEGER NOT NULL,
    original_tokens INTEGER NOT NULL,
    compressed_tokens INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- ============================================
-- INDEXES for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_last_updated ON conversations(last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_summaries_conversation_id ON summaries(conversation_id);

-- ============================================
-- TRIGGERS for auto-updates
-- ============================================

-- Auto-update last_updated when message added
CREATE TRIGGER IF NOT EXISTS update_conversation_timestamp
AFTER INSERT ON messages
BEGIN
    UPDATE conversations
    SET last_updated = datetime('now', 'localtime'),
        total_messages = total_messages + 1
    WHERE id = NEW.conversation_id;
END;

-- Auto-update total_tokens
CREATE TRIGGER IF NOT EXISTS update_conversation_tokens
AFTER INSERT ON messages
BEGIN
    UPDATE conversations
    SET total_tokens = total_tokens + COALESCE(NEW.token_count, 0)
    WHERE id = NEW.conversation_id;
END;

-- Title auto-generation is now handled in Python code
-- (after 6 messages, using first meaningful user message)
