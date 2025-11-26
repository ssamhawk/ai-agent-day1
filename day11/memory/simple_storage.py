"""
Simple Memory Storage for Day 11
SQLite-based persistent memory for conversations
"""
import sqlite3
import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from threading import Lock


class SimpleMemoryStorage:
    """
    Simple SQLite-based memory storage for conversations

    Features:
    - Thread-safe operations
    - Automatic schema creation
    - Conversation persistence
    - Message history
    - Pipeline execution tracking
    """

    def __init__(self, db_path: str = "conversations.db"):
        """
        Initialize memory storage

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self._lock = Lock()
        self.active_conversation_id = None

        # Initialize database
        self._initialize_database()
        self.logger.info(f"✅ Memory storage initialized: {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Thread-safe database connection context manager"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row  # Dict-like access
        try:
            yield conn
        finally:
            conn.close()

    def _initialize_database(self):
        """Create tables from schema if they don't exist"""
        schema_path = Path(__file__).parent / "schema.sql"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Read and execute schema
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schema = f.read()
                cursor.executescript(schema)
                conn.commit()
                self.logger.info("Database schema initialized")
            else:
                self.logger.error(f"Schema file not found: {schema_path}")
                raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # =============================================
    # CONVERSATION MANAGEMENT
    # =============================================

    def create_conversation(self, metadata: Optional[Dict] = None) -> int:
        """
        Create new conversation

        Args:
            metadata: Optional metadata dict

        Returns:
            conversation_id
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            session_id = str(uuid.uuid4())
            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute("""
                INSERT INTO conversations (session_id, metadata)
                VALUES (?, ?)
            """, (session_id, metadata_json))

            conn.commit()
            conversation_id = cursor.lastrowid

            self.active_conversation_id = conversation_id
            self.logger.info(f"Created conversation {conversation_id}")

            return conversation_id

    def get_or_create_active_conversation(self) -> int:
        """Get active conversation or create new one"""
        if self.active_conversation_id:
            return self.active_conversation_id

        # Try to load most recent conversation
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id FROM conversations
                WHERE is_archived = 0
                ORDER BY last_updated DESC
                LIMIT 1
            """)

            row = cursor.fetchone()

            if row:
                self.active_conversation_id = row['id']
                self.logger.info(f"Loaded active conversation {self.active_conversation_id}")
                return self.active_conversation_id

        # No recent conversation, create new
        return self.create_conversation()

    def get_all_conversations(self, limit: int = 100, include_archived: bool = False) -> List[Dict]:
        """
        Get all conversations with basic info

        Args:
            limit: Maximum number of conversations
            include_archived: Include archived conversations

        Returns:
            List of conversation dicts
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    id,
                    session_id,
                    title,
                    last_updated,
                    total_messages,
                    created_at,
                    total_tokens
                FROM conversations
            """

            if not include_archived:
                query += " WHERE is_archived = 0"

            query += " ORDER BY last_updated DESC LIMIT ?"

            cursor.execute(query, (limit,))

            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    'id': row['id'],
                    'session_id': row['session_id'],
                    'title': row['title'] or 'New conversation',
                    'last_updated': row['last_updated'],
                    'created_at': row['created_at'],
                    'message_count': row['total_messages'],
                    'total_tokens': row['total_tokens'],
                    'time_ago': self._format_time_ago(row['last_updated'])
                })

            return conversations

    def load_conversation_messages(self, conversation_id: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Load messages for a conversation

        Args:
            conversation_id: Conversation ID
            limit: Max messages to load (None = all)

        Returns:
            List of message dicts
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT role, content, timestamp, token_count, metadata
                FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (conversation_id,))

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'role': row['role'],
                    'content': row['content'],
                    'timestamp': row['timestamp'],
                    'token_count': row['token_count'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else None
                })

            return messages

    def update_conversation_title(self, conversation_id: int, title: str):
        """Update conversation title"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE conversations
                SET title = ?
                WHERE id = ?
            """, (title, conversation_id))

            conn.commit()
            self.logger.info(f"Updated title for conversation {conversation_id}")

    def delete_conversation(self, conversation_id: int) -> bool:
        """
        Delete conversation (CASCADE will delete related data)

        Args:
            conversation_id: Conversation to delete

        Returns:
            True if deleted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM conversations WHERE id = ?
            """, (conversation_id,))

            conn.commit()
            deleted = cursor.rowcount > 0

            if deleted:
                self.logger.info(f"Deleted conversation {conversation_id}")

                # If deleted active conversation, clear it
                if self.active_conversation_id == conversation_id:
                    self.active_conversation_id = None

            return deleted

    # =============================================
    # MESSAGE MANAGEMENT
    # =============================================

    def save_message(self, role: str, content: str, token_count: int = 0,
                    conversation_id: Optional[int] = None, metadata: Optional[Dict] = None) -> int:
        """
        Save message to database

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            token_count: Number of tokens
            conversation_id: Target conversation (None = active)
            metadata: Optional metadata dict

        Returns:
            message_id
        """
        if conversation_id is None:
            conversation_id = self.get_or_create_active_conversation()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute("""
                INSERT INTO messages (conversation_id, role, content, token_count, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (conversation_id, role, content, token_count, metadata_json))

            conn.commit()
            message_id = cursor.lastrowid

            self.logger.debug(f"Saved {role} message {message_id} ({token_count} tokens)")
            return message_id

    # =============================================
    # COMPRESSION/SUMMARIES
    # =============================================

    def save_summary(self, summary_text: str, messages_compressed: int,
                    original_tokens: int, compressed_tokens: int,
                    conversation_id: Optional[int] = None) -> int:
        """
        Save compression summary

        Args:
            summary_text: Summary text
            messages_compressed: Number of messages compressed
            original_tokens: Original token count
            compressed_tokens: Compressed token count
            conversation_id: Target conversation (None = active)

        Returns:
            summary_id
        """
        if conversation_id is None:
            conversation_id = self.get_or_create_active_conversation()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO summaries (
                    conversation_id, summary_text, messages_compressed,
                    original_tokens, compressed_tokens
                )
                VALUES (?, ?, ?, ?, ?)
            """, (conversation_id, summary_text, messages_compressed,
                  original_tokens, compressed_tokens))

            conn.commit()
            summary_id = cursor.lastrowid

            self.logger.info(f"Saved summary {summary_id}: {original_tokens}→{compressed_tokens} tokens")
            return summary_id

    def get_conversation_summaries(self, conversation_id: int) -> List[str]:
        """Get all summaries for a conversation"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT summary_text
                FROM summaries
                WHERE conversation_id = ?
                ORDER BY created_at ASC
            """, (conversation_id,))

            return [row['summary_text'] for row in cursor.fetchall()]

    # =============================================
    # PIPELINE EXECUTIONS
    # =============================================

    def save_pipeline_execution(self, query: str, result: Dict[str, Any],
                               conversation_id: Optional[int] = None) -> int:
        """
        Save pipeline execution result

        Args:
            query: User query
            result: Pipeline result dict
            conversation_id: Target conversation (None = active)

        Returns:
            execution_id
        """
        if conversation_id is None:
            conversation_id = self.get_or_create_active_conversation()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Extract data from result
            steps_json = json.dumps(result.get('steps', []))
            tools_json = json.dumps(result.get('tools_used', []))
            metadata_json = json.dumps({
                'temperature': result.get('temperature'),
                'model': result.get('model')
            })

            cursor.execute("""
                INSERT INTO pipeline_executions (
                    conversation_id, query, result, steps, tools_used,
                    success, error_message, total_steps, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation_id,
                query,
                result.get('answer', ''),
                steps_json,
                tools_json,
                result.get('success', False),
                result.get('error'),
                result.get('total_steps', 0),
                metadata_json
            ))

            conn.commit()
            execution_id = cursor.lastrowid

            self.logger.info(f"Saved pipeline execution {execution_id}")
            return execution_id

    def get_recent_pipelines(self, conversation_id: int, limit: int = 10) -> List[Dict]:
        """Get recent pipeline executions"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT query, result, tools_used, success, timestamp, total_steps
                FROM pipeline_executions
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (conversation_id, limit))

            pipelines = []
            for row in cursor.fetchall():
                pipelines.append({
                    'query': row['query'],
                    'result': row['result'],
                    'tools_used': json.loads(row['tools_used']),
                    'success': bool(row['success']),
                    'timestamp': row['timestamp'],
                    'total_steps': row['total_steps']
                })

            return pipelines

    # =============================================
    # STATISTICS & ANALYTICS
    # =============================================

    def get_stats(self) -> Dict[str, Any]:
        """Get basic statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total conversations
            cursor.execute("SELECT COUNT(*) as count FROM conversations WHERE is_archived = 0")
            total_conversations = cursor.fetchone()['count']

            # Total messages
            cursor.execute("SELECT COUNT(*) as count FROM messages")
            total_messages = cursor.fetchone()['count']

            # Total tokens
            cursor.execute("SELECT SUM(total_tokens) as sum FROM conversations")
            total_tokens = cursor.fetchone()['sum'] or 0

            # Total pipelines
            cursor.execute("SELECT COUNT(*) as count FROM pipeline_executions")
            total_pipelines = cursor.fetchone()['count']

            # Compression stats
            cursor.execute("""
                SELECT
                    SUM(original_tokens) as original,
                    SUM(compressed_tokens) as compressed
                FROM summaries
            """)
            compression_row = cursor.fetchone()

            compression_stats = {
                'original_tokens': compression_row['original'] or 0,
                'compressed_tokens': compression_row['compressed'] or 0,
                'savings_percent': 0
            }

            if compression_stats['original_tokens'] > 0:
                compression_stats['savings_percent'] = round(
                    ((compression_stats['original_tokens'] - compression_stats['compressed_tokens'])
                     / compression_stats['original_tokens']) * 100, 1
                )

            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'total_tokens': total_tokens,
                'total_pipelines': total_pipelines,
                'compression_stats': compression_stats,
                'active_conversation_id': self.active_conversation_id
            }

    # =============================================
    # UTILITY METHODS
    # =============================================

    def _format_time_ago(self, timestamp: str) -> str:
        """Format timestamp as 'X minutes ago'"""
        try:
            dt = datetime.fromisoformat(timestamp)
            now = datetime.now()
            diff = now - dt

            if diff.days > 30:
                return dt.strftime('%b %d')
            elif diff.days > 0:
                return f"{diff.days}d ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes}m ago"
            else:
                return "Just now"
        except Exception as e:
            self.logger.error(f"Error formatting time: {e}")
            return "Unknown"

    def clear_all(self) -> bool:
        """Clear all data (for testing/reset)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM pipeline_executions")
                cursor.execute("DELETE FROM summaries")
                cursor.execute("DELETE FROM messages")
                cursor.execute("DELETE FROM conversations")

                conn.commit()

                self.active_conversation_id = None
                self.logger.info("Cleared all memory data")
                return True
        except Exception as e:
            self.logger.error(f"Error clearing data: {e}")
            return False

    def export_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """Export full conversation as JSON"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get conversation
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            conv_row = cursor.fetchone()

            if not conv_row:
                return {}

            # Get messages
            messages = self.load_conversation_messages(conversation_id)

            # Get summaries
            summaries = self.get_conversation_summaries(conversation_id)

            # Get pipelines
            pipelines = self.get_recent_pipelines(conversation_id, limit=1000)

            return {
                'id': conversation_id,
                'session_id': conv_row['session_id'],
                'title': conv_row['title'],
                'created_at': conv_row['created_at'],
                'last_updated': conv_row['last_updated'],
                'total_messages': conv_row['total_messages'],
                'total_tokens': conv_row['total_tokens'],
                'metadata': json.loads(conv_row['metadata']) if conv_row['metadata'] else None,
                'messages': messages,
                'summaries': summaries,
                'pipelines': pipelines
            }
