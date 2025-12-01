"""
Indexing Routes - API endpoints for document indexing
Handles file upload, indexing, and search operations
"""
import logging
import os
from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from flask_socketio import emit
import io

logger = logging.getLogger(__name__)

# File upload configuration
ALLOWED_EXTENSIONS = {'txt', 'md', 'py', 'js', 'json', 'csv'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_type(filename):
    """Get file type from extension"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'text'
    mapping = {
        'md': 'markdown',
        'py': 'python',
        'js': 'javascript',
        'txt': 'text',
        'json': 'json',
        'csv': 'csv'
    }
    return mapping.get(ext, 'text')


def register_indexing_routes(app, socketio, indexer, vector_store, csrf):
    """
    Register indexing routes

    Args:
        app: Flask application
        socketio: SocketIO instance
        indexer: DocumentIndexer instance
        vector_store: VectorStore instance
        csrf: CSRFProtect instance
    """

    @app.route('/indexing')
    def indexing_page():
        """Render document indexing page"""
        return render_template('indexing.html')

    @app.route('/api/indexing/upload', methods=['POST'])
    @csrf.exempt
    def upload_documents():
        """
        Upload and index documents

        Expected: multipart/form-data with files
        Returns: JSON with indexing results
        """
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files[]')

        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400

        results = {
            'processed': [],
            'failed': [],
            'total_chunks': 0,
            'total_tokens': 0
        }

        for file_idx, file in enumerate(files):
            if not file or file.filename == '':
                continue

            filename = secure_filename(file.filename)

            # Check file extension
            if not allowed_file(filename):
                results['failed'].append({
                    'filename': filename,
                    'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
                })
                continue

            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            if file_size > MAX_FILE_SIZE:
                results['failed'].append({
                    'filename': filename,
                    'error': f'File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB'
                })
                continue

            try:
                # Read file content
                content = file.read().decode('utf-8')
                file_type = get_file_type(filename)

                # Emit progress
                if socketio:
                    socketio.emit('indexing_progress', {
                        'step': 'reading',
                        'filename': filename,
                        'progress': (file_idx / len(files)) * 100
                    })

                # Process document
                chunks, embeddings = indexer.process_document(
                    text=content,
                    source_file=filename,
                    file_type=file_type
                )

                if not chunks:
                    results['failed'].append({
                        'filename': filename,
                        'error': 'No chunks generated (file may be empty)'
                    })
                    continue

                # Emit progress
                if socketio:
                    socketio.emit('indexing_progress', {
                        'step': 'embedding',
                        'filename': filename,
                        'chunks': len(chunks),
                        'progress': (file_idx / len(files)) * 100
                    })

                # Add to vector store
                added = vector_store.add_documents(chunks, embeddings)

                # Calculate total tokens
                total_tokens = sum(c['metadata'].get('token_count', 0) for c in chunks)

                results['processed'].append({
                    'filename': filename,
                    'chunks': added,
                    'tokens': total_tokens,
                    'file_type': file_type
                })

                results['total_chunks'] += added
                results['total_tokens'] += total_tokens

                # Emit success
                if socketio:
                    socketio.emit('indexing_progress', {
                        'step': 'complete',
                        'filename': filename,
                        'chunks': added,
                        'progress': ((file_idx + 1) / len(files)) * 100
                    })

                logger.info(f"Indexed {filename}: {added} chunks, {total_tokens} tokens")

            except UnicodeDecodeError:
                results['failed'].append({
                    'filename': filename,
                    'error': 'Failed to decode file. Ensure it is UTF-8 encoded text.'
                })
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                results['failed'].append({
                    'filename': filename,
                    'error': str(e)
                })

        # Emit final completion
        if socketio:
            socketio.emit('indexing_complete', results)

        return jsonify(results), 200

    @app.route('/api/indexing/search', methods=['POST'])
    @csrf.exempt
    def search_documents():
        """
        Search for similar documents

        Expected JSON:
        {
            "query": "search query",
            "top_k": 5,
            "min_similarity": 0.7,
            "file_type": "markdown" (optional)
        }

        Returns: JSON with search results
        """
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400

        query = data['query']
        top_k = data.get('top_k', 5)
        min_similarity = data.get('min_similarity', 0.0)
        file_type = data.get('file_type')

        try:
            # Generate query embedding
            query_embedding = indexer.embedding_generator.generate_single_embedding(query)

            if not query_embedding:
                return jsonify({'error': 'Failed to generate query embedding'}), 500

            # Search in vector store
            results = vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                min_similarity=min_similarity,
                file_type=file_type
            )

            logger.info(f"Search query: '{query}' returned {len(results)} results")

            return jsonify({
                'query': query,
                'results': results,
                'count': len(results)
            }), 200

        except Exception as e:
            logger.error(f"Search error: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/indexing/stats', methods=['GET'])
    def get_index_stats():
        """
        Get index statistics

        Returns: JSON with index statistics
        """
        try:
            stats = vector_store.get_statistics()
            return jsonify(stats), 200
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/indexing/clear', methods=['POST'])
    @csrf.exempt
    def clear_index():
        """
        Clear entire index

        Returns: JSON with success message
        """
        try:
            vector_store.clear_index()
            logger.info("Index cleared by user")
            return jsonify({'message': 'Index cleared successfully'}), 200
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/indexing/delete/<path:filename>', methods=['DELETE'])
    @csrf.exempt
    def delete_document(filename):
        """
        Delete a document from index

        Args:
            filename: Source file name

        Returns: JSON with deletion result
        """
        try:
            deleted = vector_store.delete_by_source_file(filename)
            logger.info(f"Deleted {deleted} chunks from {filename}")
            return jsonify({
                'message': f'Deleted {deleted} chunks',
                'filename': filename,
                'deleted': deleted
            }), 200
        except Exception as e:
            logger.error(f"Error deleting {filename}: {e}")
            return jsonify({'error': str(e)}), 500

    logger.info("Indexing routes registered")
