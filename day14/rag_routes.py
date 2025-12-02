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
        Query with RAG comparison

        Request body:
        {
            "question": "User question",
            "mode": "compare" | "with_rag" | "without_rag",
            "top_k": 5,
            "min_similarity": 0.0,
            "temperature": 0.7
        }
        """
        try:
            data = request.get_json()

            if not data or 'question' not in data:
                return jsonify({'error': 'Question is required'}), 400

            question = data['question']
            mode = data.get('mode', 'compare')
            top_k = int(data.get('top_k', 5))
            min_similarity = float(data.get('min_similarity', 0.0))
            temperature = float(data.get('temperature', 0.7))

            logger.info(f"RAG query: {question} (mode={mode})")

            # Execute based on mode
            if mode == 'compare':
                result = rag_agent.compare_responses(
                    question=question,
                    top_k=top_k,
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
