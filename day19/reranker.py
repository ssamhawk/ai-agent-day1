"""
Document Reranker - Second-stage relevance scoring
Uses Cross-Encoder model to rerank retrieved documents for better relevance
"""
import logging
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class DocumentReranker:
    """
    Reranks documents using Cross-Encoder model

    Cross-Encoders provide more accurate relevance scores than bi-encoders (embeddings)
    by processing query-document pairs together.
    """

    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initialize reranker with specified model

        Popular models:
        - cross-encoder/ms-marco-MiniLM-L-6-v2 (fast, good quality)
        - cross-encoder/ms-marco-TinyBERT-L-2-v2 (fastest)
        - BAAI/bge-reranker-base (better quality, slower)

        Args:
            model_name: HuggingFace model identifier
        """
        try:
            logger.info(f"Loading Cross-Encoder model: {model_name}")
            self.model = CrossEncoder(model_name)
            self.model_name = model_name
            logger.info(f"✅ Reranker initialized: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            raise

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
        return_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on query relevance

        Args:
            query: Search query
            documents: List of document dicts with 'text' field
            top_k: Number of top documents to return
            return_scores: Whether to include rerank scores in results

        Returns:
            List of reranked documents with 'rerank_score' field
        """
        if not documents:
            logger.warning("No documents provided for reranking")
            return []

        if len(documents) <= top_k:
            logger.info(f"Document count ({len(documents)}) <= top_k ({top_k}), reranking all")

        try:
            # Create query-document pairs
            pairs = []
            for doc in documents:
                # Use 'text' or 'content' field
                text = doc.get('text') or doc.get('content', '')
                pairs.append([query, text])

            logger.info(f"Reranking {len(documents)} documents with query: '{query[:50]}...'")

            # Get relevance scores from Cross-Encoder
            scores = self.model.predict(pairs)

            # Add rerank scores and original ranks to documents
            for idx, (doc, score) in enumerate(zip(documents, scores), start=1):
                doc['rerank_score'] = float(score)
                # Store original rank for comparison (fixed O(n²) issue)
                if 'original_rank' not in doc:
                    doc['original_rank'] = idx

            # Sort by rerank score (descending)
            reranked = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)

            # Add new rank and rank change
            for new_rank, doc in enumerate(reranked, start=1):
                doc['reranked_rank'] = new_rank
                doc['rank_change'] = doc['original_rank'] - new_rank

            # Return top-k
            top_reranked = reranked[:top_k]

            # Log score statistics
            if top_reranked:
                top_score = top_reranked[0]['rerank_score']
                min_score = top_reranked[-1]['rerank_score']
                logger.info(
                    f"Reranked top-{top_k}: scores [{min_score:.3f} - {top_score:.3f}]"
                )

            return top_reranked

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback: return original documents
            return documents[:top_k]

    def compare_scores(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare original similarity scores with rerank scores

        Returns statistics for analysis
        """
        if not documents:
            return {}

        # Rerank without cutting off
        reranked = self.rerank(query, documents, top_k=len(documents))

        # Calculate statistics
        stats = {
            'total_documents': len(documents),
            'original_top_score': documents[0].get('similarity', 0),
            'reranked_top_score': reranked[0]['rerank_score'],
            'score_changes': []
        }

        # Track score changes
        for doc in reranked:
            stats['score_changes'].append({
                'original_rank': doc['original_rank'],
                'reranked_rank': doc['reranked_rank'],
                'rank_change': doc['rank_change'],
                'original_score': doc.get('similarity', 0),
                'rerank_score': doc['rerank_score']
            })

        return stats

    def filter_by_threshold(
        self,
        documents: List[Dict[str, Any]],
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Filter documents by rerank score threshold

        Args:
            documents: Documents with 'rerank_score' field
            threshold: Minimum rerank score to keep

        Returns:
            Filtered documents
        """
        filtered = [
            doc for doc in documents
            if doc.get('rerank_score', 0) >= threshold
        ]

        logger.info(
            f"Filtered {len(documents)} → {len(filtered)} documents "
            f"(threshold: {threshold})"
        )

        return filtered


# Singleton instance for reuse
_reranker_instance = None


def get_reranker(model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2') -> DocumentReranker:
    """
    Get or create reranker singleton instance

    Reuses the same model to avoid loading multiple times
    """
    global _reranker_instance

    if _reranker_instance is None or _reranker_instance.model_name != model_name:
        _reranker_instance = DocumentReranker(model_name)

    return _reranker_instance
