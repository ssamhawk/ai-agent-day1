"""
Document Indexer - Chunking and Embedding Generation
Handles document processing, text splitting, and embedding generation
"""
import logging
import tiktoken
from typing import List, Dict, Tuple
from openai import OpenAI

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Splits documents into overlapping chunks"""

    def __init__(self, chunk_size: int = 512, overlap: int = 50, model: str = "gpt-4"):
        """
        Initialize chunker

        Args:
            chunk_size: Maximum tokens per chunk
            overlap: Overlapping tokens between chunks
            model: Model name for tokenizer
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning(f"Model {model} not found, using cl100k_base encoding")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to split
            metadata: Additional metadata to attach to chunks

        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []

        # Tokenize full text
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)

        chunks = []
        start_idx = 0
        chunk_idx = 0

        while start_idx < total_tokens:
            # Get chunk tokens
            end_idx = min(start_idx + self.chunk_size, total_tokens)
            chunk_tokens = tokens[start_idx:end_idx]

            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)

            # Create chunk metadata
            chunk_meta = {
                'chunk_index': chunk_idx,
                'start_token': start_idx,
                'end_token': end_idx,
                'token_count': len(chunk_tokens),
                'total_tokens': total_tokens
            }

            # Merge with provided metadata
            if metadata:
                chunk_meta.update(metadata)

            # Add citation metadata (chunk_id for referencing)
            source_file = metadata.get('source_file', 'unknown') if metadata else 'unknown'
            chunk_meta['chunk_id'] = f"{source_file}_chunk_{chunk_idx}"

            chunks.append({
                'text': chunk_text,
                'metadata': chunk_meta
            })

            chunk_idx += 1

            # Move to next chunk with overlap
            start_idx += self.chunk_size - self.overlap

        logger.info(f"Split text into {len(chunks)} chunks (total tokens: {total_tokens})")
        return chunks


class EmbeddingGenerator:
    """Generates embeddings using OpenAI API"""

    def __init__(self, client: OpenAI, model: str = "text-embedding-3-small"):
        """
        Initialize embedding generator

        Args:
            client: OpenAI client instance
            model: Embedding model to use
        """
        self.client = client
        self.model = model
        self.dimension = 1536 if "small" in model else 3072
        logger.info(f"Initialized embedding generator with model: {model} ({self.dimension}d)")

    def generate_embeddings(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of text strings
            batch_size: Number of texts to process in one API call

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        all_embeddings = []

        # Process in batches to avoid API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model
                )

                # Extract embeddings in correct order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.info(f"Generated embeddings for batch {i//batch_size + 1} ({len(batch)} texts)")

            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Return None for failed batch items
                all_embeddings.extend([None] * len(batch))

        return all_embeddings

    def generate_single_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text string

        Returns:
            Embedding vector or None on error
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else None


class DocumentIndexer:
    """Main document indexing pipeline"""

    def __init__(self, client: OpenAI, chunk_size: int = 512, overlap: int = 50,
                 embedding_model: str = "text-embedding-3-small"):
        """
        Initialize document indexer

        Args:
            client: OpenAI client instance
            chunk_size: Maximum tokens per chunk
            overlap: Overlapping tokens between chunks
            embedding_model: Embedding model to use
        """
        self.chunker = DocumentChunker(chunk_size=chunk_size, overlap=overlap)
        self.embedding_generator = EmbeddingGenerator(client=client, model=embedding_model)
        self.chunk_size = chunk_size
        self.overlap = overlap
        logger.info("DocumentIndexer initialized")

    def process_document(self, text: str, source_file: str, file_type: str = "text") -> Tuple[List[Dict], List[List[float]]]:
        """
        Process a document: chunk and generate embeddings

        Args:
            text: Document text
            source_file: Source file name
            file_type: Type of file (text, markdown, code, etc.)

        Returns:
            Tuple of (chunks with metadata, embeddings)
        """
        logger.info(f"Processing document: {source_file}")

        # Add file metadata
        file_metadata = {
            'source_file': source_file,
            'file_type': file_type
        }

        # Chunk document
        chunks = self.chunker.chunk_text(text, metadata=file_metadata)

        if not chunks:
            logger.warning(f"No chunks generated for {source_file}")
            return [], []

        # Extract texts for embedding
        chunk_texts = [chunk['text'] for chunk in chunks]

        # Generate embeddings
        embeddings = self.embedding_generator.generate_embeddings(chunk_texts)

        # Filter out failed embeddings
        valid_chunks = []
        valid_embeddings = []

        for chunk, embedding in zip(chunks, embeddings):
            if embedding is not None:
                valid_chunks.append(chunk)
                valid_embeddings.append(embedding)

        logger.info(f"Successfully processed {source_file}: {len(valid_chunks)} chunks with embeddings")

        return valid_chunks, valid_embeddings

    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.embedding_generator.dimension
