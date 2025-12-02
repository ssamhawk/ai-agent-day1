"""
RAG Agent - Retrieval-Augmented Generation
Compares LLM responses with and without document context
"""
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from vector_store import VectorStore
from document_indexer import EmbeddingGenerator
from reranker import get_reranker

logger = logging.getLogger(__name__)


class RAGAgent:
    """Agent that can query with and without RAG"""

    def __init__(
        self,
        client: OpenAI,
        vector_store: VectorStore,
        embedding_generator: EmbeddingGenerator,
        model: str = "gpt-4o-mini",
        enable_reranking: bool = True
    ):
        """
        Initialize RAG Agent

        Args:
            client: OpenAI client
            vector_store: Vector store for document retrieval
            embedding_generator: Embedding generator for queries
            model: LLM model to use
            enable_reranking: Whether to enable reranker
        """
        self.client = client
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.model = model

        # Initialize reranker
        self.reranker = None
        if enable_reranking:
            try:
                self.reranker = get_reranker()
                logger.info("✅ Reranker enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize reranker: {e}")
                self.reranker = None

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

    def query_with_rag_reranking(
        self,
        question: str,
        top_k_retrieve: int = 20,
        top_k_final: int = 5,
        min_similarity: float = 0.0,
        temperature: float = 0.7,
        rerank_threshold: float = None
    ) -> Dict:
        """
        Query LLM with retrieved and reranked document context (RAG + Reranking)

        Pipeline:
        1. Retrieve top_k_retrieve documents (e.g., 20)
        2. Filter by min_similarity threshold
        3. Rerank using Cross-Encoder
        4. Take top_k_final documents (e.g., 5)
        5. Generate answer with context

        Args:
            question: User question
            top_k_retrieve: Number of chunks to retrieve initially
            top_k_final: Number of chunks to use after reranking
            min_similarity: Minimum similarity threshold for initial retrieval
            temperature: LLM temperature
            rerank_threshold: Optional minimum rerank score threshold

        Returns:
            Dictionary with response and reranking metadata
        """
        logger.info(
            f"Query with RAG + Reranking: {question} "
            f"(retrieve={top_k_retrieve}, final={top_k_final}, min_sim={min_similarity})"
        )

        if not self.reranker:
            logger.warning("Reranker not available, falling back to regular RAG")
            return self.query_with_rag(question, top_k_final, min_similarity, temperature)

        try:
            # Step 1: Generate query embedding
            query_embedding = self.embedding_generator.generate_single_embedding(question)

            # Step 2: Retrieve more documents than needed
            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k_retrieve,
                min_similarity=min_similarity
            )

            logger.info(f"Retrieved {len(search_results)} chunks before reranking")

            if not search_results:
                return {
                    'answer': "No relevant documents found in the knowledge base.",
                    'tokens_used': 0,
                    'mode': 'with_rag_reranking',
                    'chunks_used': [],
                    'source_files': [],
                    'reranking_applied': True,
                    'chunks_before_rerank': 0,
                    'chunks_after_rerank': 0
                }

            # Step 3: Rerank documents
            reranked_results = self.reranker.rerank(
                query=question,
                documents=search_results,
                top_k=top_k_final
            )

            # Step 4: Optional threshold filtering after reranking
            if rerank_threshold is not None:
                reranked_results = [
                    doc for doc in reranked_results
                    if doc.get('rerank_score', 0) >= rerank_threshold
                ]

            logger.info(
                f"After reranking: {len(reranked_results)} chunks "
                f"(filtered from {len(search_results)})"
            )

            # Step 5: Build context from reranked chunks
            context_parts = []
            chunks_used = []
            source_files = set()

            for i, result in enumerate(reranked_results, 1):
                source_file = result['source_file']
                text = result['text']
                similarity = result['similarity']
                rerank_score = result.get('rerank_score', 0)
                rank_change = result.get('rank_change', 0)

                # Show both scores in context
                context_parts.append(
                    f"[Document {i}: {source_file}]\n"
                    f"[Similarity: {similarity:.2%} | Rerank Score: {rerank_score:.3f} | Rank Change: {rank_change:+d}]\n"
                    f"{text}\n"
                )

                chunks_used.append({
                    'source_file': source_file,
                    'text': text,
                    'similarity': similarity,
                    'rerank_score': rerank_score,
                    'original_rank': result.get('original_rank', 0),
                    'reranked_rank': result.get('reranked_rank', 0),
                    'rank_change': rank_change,
                    'chunk_index': result['chunk_index'],
                    'token_count': result['token_count']
                })

                source_files.add(source_file)

            context = "\n".join(context_parts)
            source_files = list(source_files)

            # Step 6: Build prompt with context
            system_prompt = """You are a helpful assistant that answers questions based on the provided documents.

Instructions:
- Use the documents below to answer the user's question
- Documents are ranked by relevance (most relevant first)
- If the documents contain relevant information, use it in your answer
- If the documents don't contain enough information, say so and provide what you can
- Cite which document(s) you used in your answer
- Be concise and accurate"""

            user_prompt = f"""Based on the following documents, please answer this question:

Question: {question}

Documents (ranked by relevance):
{context}

Answer:"""

            # Step 7: Query LLM with reranked context
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

            logger.info(
                f"Response with RAG+Reranking: {len(answer)} chars, "
                f"{tokens_used} tokens, {len(chunks_used)} chunks"
            )

            return {
                'answer': answer,
                'tokens_used': tokens_used,
                'mode': 'with_rag_reranking',
                'chunks_used': chunks_used,
                'source_files': source_files,
                'num_chunks': len(chunks_used),
                'reranking_applied': True,
                'chunks_before_rerank': len(search_results),
                'chunks_after_rerank': len(reranked_results)
            }

        except Exception as e:
            logger.error(f"Error in query_with_rag_reranking: {e}")
            return {
                'answer': f"Error: {str(e)}",
                'tokens_used': 0,
                'mode': 'with_rag_reranking',
                'chunks_used': [],
                'source_files': [],
                'reranking_applied': False,
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

    def compare_with_reranking(
        self,
        question: str,
        top_k_retrieve: int = 20,
        top_k_final: int = 5,
        min_similarity: float = 0.0,
        temperature: float = 0.7
    ) -> Dict:
        """
        Compare RAG responses without and with reranking

        FIXED: Now uses SAME initial retrieval for fair comparison!

        Args:
            question: User question
            top_k_retrieve: Number of chunks to retrieve initially
            top_k_final: Number of chunks to use after filtering/reranking
            min_similarity: Minimum similarity threshold
            temperature: LLM temperature

        Returns:
            Dictionary with both responses and reranking comparison
        """
        logger.info(f"Comparing RAG with/without reranking for: {question}")

        if not self.reranker:
            logger.warning("Reranker not available, using standard comparison")
            return self.compare_responses(question, top_k_final, min_similarity, temperature)

        try:
            # Step 1: ONE retrieval for BOTH comparisons (fair comparison!)
            query_embedding = self.embedding_generator.generate_single_embedding(question)

            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k_retrieve,  # Get 20 documents
                min_similarity=min_similarity
            )

            logger.info(f"Retrieved {len(search_results)} chunks for comparison")

            if not search_results:
                empty_response = {
                    'answer': "No relevant documents found in the knowledge base.",
                    'tokens_used': 0,
                    'chunks_used': [],
                    'source_files': [],
                    'num_chunks': 0
                }
                return {
                    'question': question,
                    'without_reranking': empty_response,
                    'with_reranking': empty_response,
                    'comparison': {}
                }

            # Step 2: WITHOUT reranking - TOP-5 by embedding similarity (first 5 of 20)
            top_without_rerank = search_results[:top_k_final]

            # Step 3: WITH reranking - rerank all 20, then TOP-5
            search_results_copy = [dict(doc) for doc in search_results]  # Deep copy
            top_with_rerank = self.reranker.rerank(
                query=question,
                documents=search_results_copy,
                top_k=top_k_final
            )

            logger.info(
                f"Without reranking: {len(top_without_rerank)} chunks | "
                f"With reranking: {len(top_with_rerank)} chunks"
            )

            # Step 4: Generate responses for BOTH sets
            response_without_rerank = self._generate_response_from_chunks(
                question=question,
                chunks=top_without_rerank,
                temperature=temperature,
                mode='without_reranking'
            )

            response_with_rerank = self._generate_response_from_chunks(
                question=question,
                chunks=top_with_rerank,
                temperature=temperature,
                mode='with_reranking'
            )

            # Step 5: Compare results
            without_chunks = response_without_rerank.get('chunks_used', [])
            with_chunks = response_with_rerank.get('chunks_used', [])

            return {
                'question': question,
                'without_reranking': response_without_rerank,
                'with_reranking': response_with_rerank,
                'comparison': {
                    'chunks_retrieved': len(without_chunks),
                    'chunks_after_rerank': len(with_chunks),
                    'source_files_without': response_without_rerank.get('source_files', []),
                    'source_files_with': response_with_rerank.get('source_files', []),
                    'reranking_improved': self._calculate_rerank_improvement(without_chunks, with_chunks)
                }
            }

        except Exception as e:
            logger.error(f"Error in compare_with_reranking: {e}")
            return {
                'question': question,
                'without_reranking': {'answer': f"Error: {str(e)}", 'tokens_used': 0, 'chunks_used': [], 'source_files': []},
                'with_reranking': {'answer': f"Error: {str(e)}", 'tokens_used': 0, 'chunks_used': [], 'source_files': []},
                'comparison': {},
                'error': str(e)
            }

    def _generate_response_from_chunks(
        self,
        question: str,
        chunks: List[Dict],
        temperature: float,
        mode: str
    ) -> Dict:
        """
        Generate LLM response from given chunks

        Args:
            question: User question
            chunks: List of document chunks
            temperature: LLM temperature
            mode: Response mode identifier

        Returns:
            Dictionary with response and metadata
        """
        try:
            # Build context from chunks
            if not chunks:
                context = "No relevant documents found."
                chunks_used = []
                source_files = []
            else:
                context_parts = []
                chunks_used = []
                source_files = set()

                for i, result in enumerate(chunks, 1):
                    source_file = result['source_file']
                    text = result['text']
                    similarity = result['similarity']

                    # Check if rerank info is available
                    if 'rerank_score' in result:
                        rerank_score = result['rerank_score']
                        rank_change = result.get('rank_change', 0)
                        context_parts.append(
                            f"[Document {i}: {source_file}]\n"
                            f"[Similarity: {similarity:.2%} | Rerank: {rerank_score:.3f} | Change: {rank_change:+d}]\n"
                            f"{text}\n"
                        )
                    else:
                        context_parts.append(
                            f"[Document {i}: {source_file} (relevance: {similarity:.2%})]\n{text}\n"
                        )

                    chunks_used.append({
                        'source_file': source_file,
                        'text': text,
                        'similarity': similarity,
                        'chunk_index': result['chunk_index'],
                        'token_count': result['token_count'],
                        **(
                            {
                                'rerank_score': result['rerank_score'],
                                'original_rank': result.get('original_rank', 0),
                                'reranked_rank': result.get('reranked_rank', 0),
                                'rank_change': result.get('rank_change', 0)
                            } if 'rerank_score' in result else {}
                        )
                    })

                    source_files.add(source_file)

                context = "\n".join(context_parts)
                source_files = list(source_files)

            # Build prompt
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

            # Query LLM
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

            return {
                'answer': answer,
                'tokens_used': tokens_used,
                'mode': mode,
                'chunks_used': chunks_used,
                'source_files': source_files,
                'num_chunks': len(chunks_used)
            }

        except Exception as e:
            logger.error(f"Error generating response from chunks: {e}")
            return {
                'answer': f"Error: {str(e)}",
                'tokens_used': 0,
                'mode': mode,
                'chunks_used': [],
                'source_files': [],
                'error': str(e)
            }

    def _calculate_rerank_improvement(self, chunks_without, chunks_with) -> Dict:
        """Calculate metrics showing reranking improvement"""
        if not chunks_without or not chunks_with:
            return {}

        # Average similarity before reranking
        avg_sim_before = sum(c.get('similarity', 0) for c in chunks_without) / len(chunks_without)

        # Average rerank score after reranking
        avg_rerank_score = sum(c.get('rerank_score', 0) for c in chunks_with) / len(chunks_with)

        # Count rank changes
        improved = sum(1 for c in chunks_with if c.get('rank_change', 0) > 0)
        worsened = sum(1 for c in chunks_with if c.get('rank_change', 0) < 0)

        return {
            'avg_similarity_before': avg_sim_before,
            'avg_rerank_score_after': avg_rerank_score,
            'chunks_improved_rank': improved,
            'chunks_worsened_rank': worsened,
            'total_rank_changes': improved + worsened
        }
