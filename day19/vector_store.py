"""
Vector Store - FAISS Index + SQLite Metadata
Handles vector storage, similarity search, and metadata management
"""
import logging
import sqlite3
import json
import numpy as np
import faiss
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store with SQLite metadata"""

    def __init__(self, db_path: str = "vector_index.db", dimension: int = 1536):
        """
        Initialize vector store

        Args:
            db_path: Path to SQLite database
            dimension: Embedding vector dimension
        """
        self.db_path = db_path
        self.dimension = dimension
        self.index = None
        self.conn = None
        self.index_to_id = []  # Maps FAISS index to DB row ID
        self.faiss_index_path = db_path.replace('.db', '.faiss')

        # Initialize
        self._init_database()
        self._init_faiss_index()
        self._load_existing_mappings()

        logger.info(f"VectorStore initialized (dimension: {dimension}, db: {db_path})")

    def _init_faiss_index(self):
        """Initialize FAISS index with cosine similarity"""
        import os

        # Try to load existing index from disk
        if os.path.exists(self.faiss_index_path):
            try:
                self.index = faiss.read_index(self.faiss_index_path)
                logger.info(f"Loaded existing FAISS index from {self.faiss_index_path} ({self.index.ntotal} vectors)")
                return
            except Exception as e:
                logger.warning(f"Failed to load FAISS index from {self.faiss_index_path}: {e}")

        # Create new index if loading failed or file doesn't exist
        self.index = faiss.IndexFlatIP(self.dimension)
        logger.info("Created new FAISS index")

    def _init_database(self):
        """Initialize SQLite database for metadata"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()

        # Create documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE NOT NULL,
                source_file TEXT NOT NULL,
                file_type TEXT,
                chunk_text TEXT NOT NULL,
                chunk_index INTEGER,
                token_count INTEGER,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create index on chunk_id for fast lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chunk_id ON documents(chunk_id)
        ''')

        # Create index on source_file for filtering
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_source_file ON documents(source_file)
        ''')

        self.conn.commit()
        logger.info("SQLite database initialized")

    def _load_existing_mappings(self):
        """Load existing ID mappings from database"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM documents ORDER BY id')
        rows = cursor.fetchall()
        self.index_to_id = [row[0] for row in rows]
        if self.index_to_id:
            logger.info(f"Loaded {len(self.index_to_id)} existing ID mappings")

    def _generate_chunk_id(self, source_file: str, chunk_index: int) -> str:
        """Generate unique chunk ID"""
        content = f"{source_file}_{chunk_index}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()

    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """Normalize vectors for cosine similarity"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1
        return vectors / norms

    def _save_faiss_index(self):
        """Save FAISS index to disk"""
        try:
            faiss.write_index(self.index, self.faiss_index_path)
            logger.info(f"FAISS index saved to {self.faiss_index_path}")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def add_documents(self, chunks: List[Dict], embeddings: List[List[float]]) -> int:
        """
        Add documents to the index

        Args:
            chunks: List of chunk dictionaries with text and metadata
            embeddings: List of embedding vectors

        Returns:
            Number of documents added
        """
        if not chunks or not embeddings:
            logger.warning("No chunks or embeddings provided")
            return 0

        if len(chunks) != len(embeddings):
            logger.error(f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings")
            return 0

        # Convert to numpy array and normalize
        vectors = np.array(embeddings, dtype=np.float32)
        vectors = self._normalize_vectors(vectors)

        # Add to FAISS index
        self.index.add(vectors)

        # Add metadata to SQLite
        cursor = self.conn.cursor()
        added = 0

        for chunk, embedding in zip(chunks, embeddings):
            try:
                metadata = chunk.get('metadata', {})
                chunk_id = self._generate_chunk_id(
                    metadata.get('source_file', 'unknown'),
                    metadata.get('chunk_index', 0)
                )

                cursor.execute('''
                    INSERT INTO documents
                    (chunk_id, source_file, file_type, chunk_text, chunk_index, token_count, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chunk_id,
                    metadata.get('source_file', ''),
                    metadata.get('file_type', 'text'),
                    chunk['text'],
                    metadata.get('chunk_index', 0),
                    metadata.get('token_count', 0),
                    json.dumps(metadata)
                ))

                # Get the ID of inserted row and add to mapping
                row_id = cursor.lastrowid
                self.index_to_id.append(row_id)
                added += 1

            except sqlite3.IntegrityError:
                logger.warning(f"Duplicate chunk_id, skipping: {chunk_id}")
            except Exception as e:
                logger.error(f"Error adding document: {e}")

        self.conn.commit()

        # Save FAISS index to disk
        self._save_faiss_index()

        logger.info(f"Added {added} documents to index")

        return added

    def search(self, query_embedding: List[float], top_k: int = 5,
               min_similarity: float = 0.0, file_type: str = None) -> List[Dict]:
        """
        Search for similar documents

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)
            file_type: Optional file type filter

        Returns:
            List of result dictionaries with text, metadata, and similarity score
        """
        if self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []

        # Normalize query vector
        query_vector = np.array([query_embedding], dtype=np.float32)
        query_vector = self._normalize_vectors(query_vector)

        # Search in FAISS
        distances, indices = self.index.search(query_vector, min(top_k * 2, self.index.ntotal))

        logger.info(f"FAISS search returned {len(indices[0])} candidates")
        logger.info(f"Distances: {distances[0][:5]}")  # Log first 5 distances
        logger.info(f"Indices: {indices[0][:5]}")  # Log first 5 indices

        # Get metadata from SQLite
        results = []
        cursor = self.conn.cursor()

        for distance, idx in zip(distances[0], indices[0]):
            # FAISS returns -1 for invalid indices
            if idx == -1:
                logger.info(f"Skipping invalid index: -1")
                continue

            # Cosine similarity (since we normalized vectors)
            similarity = float(distance)
            logger.info(f"Processing idx={idx}, similarity={similarity:.4f}, min_threshold={min_similarity}")

            # Filter by minimum similarity
            if similarity < min_similarity:
                logger.info(f"Filtered out idx={idx} due to low similarity: {similarity:.4f} < {min_similarity}")
                continue

            # Get DB row ID from mapping
            if idx >= len(self.index_to_id):
                logger.warning(f"Index {idx} out of range for index_to_id mapping (len={len(self.index_to_id)})")
                continue

            row_id = self.index_to_id[idx]
            logger.info(f"Mapped FAISS idx={idx} to DB row_id={row_id}")

            # Get document metadata by ID
            cursor.execute('''
                SELECT chunk_id, source_file, file_type, chunk_text, chunk_index,
                       token_count, metadata, created_at
                FROM documents
                WHERE id = ?
            ''', (row_id,))

            row = cursor.fetchone()
            if not row:
                logger.warning(f"No row found for ID {row_id}")
                continue

            # Parse metadata
            try:
                metadata = json.loads(row[6]) if row[6] else {}
            except json.JSONDecodeError:
                metadata = {}

            # Filter by file type if specified
            if file_type and row[2] != file_type:
                continue

            results.append({
                'chunk_id': row[0],
                'source_file': row[1],
                'file_type': row[2],
                'text': row[3],
                'chunk_index': row[4],
                'token_count': row[5],
                'metadata': metadata,
                'similarity': similarity,
                'created_at': row[7]
            })

            # Break if we have enough results
            if len(results) >= top_k:
                break

        logger.info(f"Search returned {len(results)} results")
        return results

    def get_statistics(self) -> Dict:
        """
        Get index statistics

        Returns:
            Dictionary with index statistics
        """
        cursor = self.conn.cursor()

        # Total documents
        cursor.execute('SELECT COUNT(*) FROM documents')
        total_docs = cursor.fetchone()[0]

        # Documents by file
        cursor.execute('''
            SELECT source_file, COUNT(*), SUM(token_count)
            FROM documents
            GROUP BY source_file
        ''')
        files = cursor.fetchall()

        # Documents by file type
        cursor.execute('''
            SELECT file_type, COUNT(*)
            FROM documents
            GROUP BY file_type
        ''')
        file_types = cursor.fetchall()

        # Total tokens
        cursor.execute('SELECT SUM(token_count) FROM documents')
        total_tokens = cursor.fetchone()[0] or 0

        return {
            'total_chunks': total_docs,
            'total_tokens': total_tokens,
            'total_files': len(files),
            'files': [{'name': f[0], 'chunks': f[1], 'tokens': f[2]} for f in files],
            'file_types': {ft[0]: ft[1] for ft in file_types},
            'index_size': self.index.ntotal,
            'dimension': self.dimension
        }

    def clear_index(self):
        """Clear entire index"""
        import os

        # Reset FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)

        # Delete FAISS index file
        if os.path.exists(self.faiss_index_path):
            try:
                os.remove(self.faiss_index_path)
                logger.info(f"Deleted FAISS index file: {self.faiss_index_path}")
            except Exception as e:
                logger.error(f"Failed to delete FAISS index file: {e}")

        # Clear database
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM documents')
        self.conn.commit()

        # Clear mapping
        self.index_to_id = []

        logger.info("Index cleared")

    def delete_by_source_file(self, source_file: str) -> int:
        """
        Delete all chunks from a specific source file
        Note: This doesn't remove from FAISS index (requires rebuild)

        Args:
            source_file: Source file name

        Returns:
            Number of chunks deleted
        """
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM documents WHERE source_file = ?', (source_file,))
        deleted = cursor.rowcount
        self.conn.commit()

        logger.info(f"Deleted {deleted} chunks from {source_file}")
        logger.warning("FAISS index not updated - consider rebuilding for accuracy")

        return deleted

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __del__(self):
        """Cleanup on deletion"""
        self.close()
