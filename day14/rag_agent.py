"""
RAG Agent - Retrieval-Augmented Generation
Compares LLM responses with and without document context
"""
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from vector_store import VectorStore
from document_indexer import EmbeddingGenerator

logger = logging.getLogger(__name__)


class RAGAgent:
    """Agent that can query with and without RAG"""

    def __init__(
        self,
        client: OpenAI,
        vector_store: VectorStore,
        embedding_generator: EmbeddingGenerator,
        model: str = "gpt-4o-mini"
    ):
        """
        Initialize RAG Agent

        Args:
            client: OpenAI client
            vector_store: Vector store for document retrieval
            embedding_generator: Embedding generator for queries
            model: LLM model to use
        """
        self.client = client
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.model = model
        logger.info(f"RAGAgent initialized with model: {model}")

    def query_without_rag(self, question: str, temperature: float = 0.7) -> Dict:
        """
        Query LLM directly without document context

        Args:
            question: User question
            temperature: LLM temperature

        Returns:
            Dictionary with response and metadata
        """
        logger.info(f"Query without RAG: {question}")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Answer the user's question based on your general knowledge."
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                temperature=temperature
            )

            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            logger.info(f"Response without RAG: {len(answer)} chars, {tokens_used} tokens")

            return {
                'answer': answer,
                'tokens_used': tokens_used,
                'mode': 'without_rag',
                'chunks_used': [],
                'source_files': []
            }

        except Exception as e:
            logger.error(f"Error in query_without_rag: {e}")
            return {
                'answer': f"Error: {str(e)}",
                'tokens_used': 0,
                'mode': 'without_rag',
                'chunks_used': [],
                'source_files': [],
                'error': str(e)
            }

    def query_with_rag(
        self,
        question: str,
        top_k: int = 5,
        min_similarity: float = 0.0,
        temperature: float = 0.7
    ) -> Dict:
        """
        Query LLM with retrieved document context (RAG)

        Args:
            question: User question
            top_k: Number of chunks to retrieve
            min_similarity: Minimum similarity threshold
            temperature: LLM temperature

        Returns:
            Dictionary with response and metadata
        """
        logger.info(f"Query with RAG: {question} (top_k={top_k}, min_sim={min_similarity})")

        try:
            # Step 1: Generate query embedding
            query_embedding = self.embedding_generator.generate_single_embedding(question)

            # Step 2: Search for relevant chunks
            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                min_similarity=min_similarity
            )

            logger.info(f"Retrieved {len(search_results)} chunks")

            # Step 3: Build context from retrieved chunks
            if not search_results:
                context = "No relevant documents found in the knowledge base."
                chunks_used = []
                source_files = []
            else:
                context_parts = []
                chunks_used = []
                source_files = set()

                for i, result in enumerate(search_results, 1):
                    source_file = result['source_file']
                    text = result['text']
                    similarity = result['similarity']

                    context_parts.append(
                        f"[Document {i}: {source_file} (relevance: {similarity:.2%})]\n{text}\n"
                    )

                    chunks_used.append({
                        'source_file': source_file,
                        'text': text,
                        'similarity': similarity,
                        'chunk_index': result['chunk_index'],
                        'token_count': result['token_count']
                    })

                    source_files.add(source_file)

                context = "\n".join(context_parts)
                source_files = list(source_files)

            # Step 4: Build prompt with context
            system_prompt = """You are a helpful assistant that answers questions based on the provided documents.

Instructions:
- Use the documents below to answer the user's question
- If the documents contain relevant information, use it in your answer
- If the documents don't contain enough information, say so and provide what you can
- Cite which document(s) you used in your answer
- Be concise and accurate"""

            user_prompt = f"""Based on the following documents, please answer this question:

Question: {question}

Documents:
{context}

Answer:"""

            # Step 5: Query LLM with context
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )

            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            logger.info(f"Response with RAG: {len(answer)} chars, {tokens_used} tokens, {len(chunks_used)} chunks")

            return {
                'answer': answer,
                'tokens_used': tokens_used,
                'mode': 'with_rag',
                'chunks_used': chunks_used,
                'source_files': source_files,
                'num_chunks': len(chunks_used)
            }

        except Exception as e:
            logger.error(f"Error in query_with_rag: {e}")
            return {
                'answer': f"Error: {str(e)}",
                'tokens_used': 0,
                'mode': 'with_rag',
                'chunks_used': [],
                'source_files': [],
                'error': str(e)
            }

    def compare_responses(
        self,
        question: str,
        top_k: int = 5,
        min_similarity: float = 0.0,
        temperature: float = 0.7
    ) -> Dict:
        """
        Compare responses with and without RAG

        Args:
            question: User question
            top_k: Number of chunks to retrieve for RAG
            min_similarity: Minimum similarity threshold for RAG
            temperature: LLM temperature

        Returns:
            Dictionary with both responses and comparison metadata
        """
        logger.info(f"Comparing RAG responses for: {question}")

        # Get both responses
        response_without_rag = self.query_without_rag(question, temperature)
        response_with_rag = self.query_with_rag(question, top_k, min_similarity, temperature)

        return {
            'question': question,
            'without_rag': response_without_rag,
            'with_rag': response_with_rag,
            'comparison': {
                'chunks_retrieved': len(response_with_rag.get('chunks_used', [])),
                'source_files': response_with_rag.get('source_files', []),
                'tokens_saved': response_without_rag.get('tokens_used', 0) - response_with_rag.get('tokens_used', 0)
            }
        }
