"""
RAG Routes - API endpoints for RAG comparison
"""
import logging
from flask import jsonify, request, render_template

logger = logging.getLogger(__name__)


def register_rag_routes(app, rag_agent, csrf):
    """Register RAG-specific routes"""

    @app.route('/rag')
    def rag_page():
        """RAG comparison page"""
        return render_template('rag.html')

    @app.route('/api/rag/query', methods=['POST'])
    @csrf.exempt
    def rag_query():
        """
        Query with RAG comparison and optional reranking

        Request body:
        {
            "question": "User question",
            "mode": "compare" | "compare_reranking" | "with_rag" | "without_rag" | "with_reranking",
            "top_k": 5,
            "top_k_retrieve": 20,  # For reranking mode
            "min_similarity": 0.0,
            "temperature": 0.7,
            "enable_reranking": true
        }
        """
        try:
            data = request.get_json()

            if not data or 'question' not in data:
                return jsonify({'error': 'Question is required'}), 400

            question = data['question']
            mode = data.get('mode', 'compare')
            top_k = int(data.get('top_k', 5))
            top_k_retrieve = int(data.get('top_k_retrieve', 20))
            min_similarity = float(data.get('min_similarity', 0.0))
            temperature = float(data.get('temperature', 0.7))
            enable_reranking = data.get('enable_reranking', False)

            logger.info(
                f"RAG query: {question} (mode={mode}, reranking={enable_reranking})"
            )

            # Execute based on mode
            if mode == 'compare':
                result = rag_agent.compare_responses(
                    question=question,
                    top_k=top_k,
                    min_similarity=min_similarity,
                    temperature=temperature
                )
            elif mode == 'compare_reranking':
                # Compare RAG without vs with reranking
                result = rag_agent.compare_with_reranking(
                    question=question,
                    top_k_retrieve=top_k_retrieve,
                    top_k_final=top_k,
                    min_similarity=min_similarity,
                    temperature=temperature
                )
            elif mode == 'with_rag':
                response = rag_agent.query_with_rag(
                    question=question,
                    top_k=top_k,
                    min_similarity=min_similarity,
                    temperature=temperature
                )
                result = {
                    'question': question,
                    'with_rag': response
                }
            elif mode == 'with_reranking':
                # Query with reranking enabled
                response = rag_agent.query_with_rag_reranking(
                    question=question,
                    top_k_retrieve=top_k_retrieve,
                    top_k_final=top_k,
                    min_similarity=min_similarity,
                    temperature=temperature
                )
                result = {
                    'question': question,
                    'with_reranking': response
                }
            elif mode == 'without_rag':
                response = rag_agent.query_without_rag(
                    question=question,
                    temperature=temperature
                )
                result = {
                    'question': question,
                    'without_rag': response
                }
            else:
                return jsonify({'error': f'Invalid mode: {mode}'}), 400

            return jsonify(result)

        except Exception as e:
            logger.error(f"Error in rag_query: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    logger.info("RAG routes registered")
