"""
Routes module for Day 10 AI Application
Handles all HTTP routes and WebSocket event handlers
"""
import os
import logging
from flask import render_template, request, jsonify, session
from flask_socketio import emit
from flask_wtf.csrf import generate_csrf
from ai_service import get_ai_response
from compression import get_conversation_state, count_tokens, count_messages_tokens
from config import (
    OPENAI_TEMPERATURE,
    OPENAI_MAX_TOKENS,
    MAX_MESSAGE_LENGTH,
    DEFAULT_COMPRESSION_THRESHOLD,
    DEFAULT_RECENT_KEEP
)
from mcp_client import mcp_client
from pipeline_agent import get_pipeline_agent

# Module logger
logger = logging.getLogger(__name__)


def register_routes(app, limiter, client, memory_storage):
    """
    Register all Flask routes with the app

    Args:
        app: Flask application instance
        limiter: Flask-Limiter instance
        client: OpenAI client
        memory_storage: Memory storage instance
    """

    @app.after_request
    def set_security_headers(response):
        """Add security headers with dynamic port support"""
        # Get current port from environment
        port = os.getenv('FLASK_PORT', '5010')
        host = os.getenv('FLASK_HOST', '127.0.0.1')

        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' https://cdn.socket.io; "
            f"connect-src 'self' ws://{host}:{port} ws://localhost:{port};"
        )
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    @app.route('/')
    def home():
        """Main page"""
        return render_template('index.html')

    @app.route('/api/csrf-token', methods=['GET'])
    def get_csrf_token():
        """Get CSRF token"""
        return jsonify({'csrf_token': generate_csrf()})

    @app.route('/api/chat', methods=['POST'])
    @limiter.limit("10 per minute")
    def chat():
        """Chat endpoint with compression support"""
        try:
            data = request.get_json()

            if not data or 'message' not in data:
                return jsonify({'error': 'Missing message', 'success': False}), 400

            user_message = data['message'].strip()
            temperature = data.get('temperature', OPENAI_TEMPERATURE)
            response_format = data.get('format', 'plain').lower()
            fields = data.get('fields')
            intelligent_mode = data.get('intelligent_mode', False)
            max_tokens = data.get('max_tokens', OPENAI_MAX_TOKENS)

            # Compression settings
            compression_enabled = data.get('compression_enabled', True)
            compression_threshold = data.get('compression_threshold', DEFAULT_COMPRESSION_THRESHOLD)
            keep_recent = data.get('keep_recent', DEFAULT_RECENT_KEEP)

            # Conversation ID from frontend
            conversation_id = data.get('conversation_id')

            # Validate inputs
            if not user_message:
                return jsonify({'error': 'Message cannot be empty', 'success': False}), 400

            if len(user_message) > MAX_MESSAGE_LENGTH:
                return jsonify({'error': f'Message too long (max {MAX_MESSAGE_LENGTH})', 'success': False}), 400

            # Validate temperature
            try:
                temperature = float(temperature)
                if not 0 <= temperature <= 2:
                    return jsonify({'error': 'Temperature must be 0-2', 'success': False}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid temperature', 'success': False}), 400

            # Validate max_tokens
            try:
                max_tokens = int(max_tokens)
                if not 1 <= max_tokens <= 16384:
                    return jsonify({'error': 'Max tokens must be 1-16384', 'success': False}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid max_tokens', 'success': False}), 400

            # Validate compression settings
            try:
                compression_threshold = int(compression_threshold)
                keep_recent = int(keep_recent)
                if compression_threshold < 2:
                    compression_threshold = 2
                if keep_recent < 0:
                    keep_recent = 0
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid compression settings', 'success': False}), 400

            # Set active conversation if provided from frontend
            if conversation_id and memory_storage:
                memory_storage.active_conversation_id = conversation_id
                logger.info(f"Using conversation ID from frontend: {conversation_id}")

            # Get AI response
            result = get_ai_response(
                user_message, response_format, fields, temperature, intelligent_mode, max_tokens,
                compression_enabled, compression_threshold, keep_recent
            )

            return jsonify({
                'response': result['response'],
                'format': response_format,
                'tokens': result['tokens'],
                'compression_stats': result['compression_stats'],
                'truncated': result['truncated'],
                'temperature': temperature,
                'success': True
            })

        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/api/clear', methods=['POST'])
    def clear_conversation():
        """Clear conversation and reset compression state"""
        try:
            session['conversation_state'] = {
                'summaries': [],
                'recent_messages': [],
                'total_messages': 0,
                'stats': {
                    'original_tokens': 0,
                    'compressed_tokens': 0,
                    'savings_percent': 0
                }
            }
            session.modified = True
            return jsonify({'success': True, 'message': 'Conversation cleared'})
        except Exception as e:
            logger.error(f"Error clearing: {str(e)}")
            return jsonify({'error': 'Failed to clear', 'success': False}), 500

    @app.route('/api/compression-stats', methods=['GET'])
    def get_compression_stats():
        """Get current compression statistics"""
        try:
            state = get_conversation_state()

            # Calculate tokens for summaries
            summaries_tokens = sum(count_tokens(s) for s in state['summaries'])

            # Calculate tokens for recent messages
            recent_tokens = count_messages_tokens(state['recent_messages'])

            # Calculate actual context size (what we're really using)
            actual_context_tokens = summaries_tokens + recent_tokens

            # Calculate what it would be without compression
            original_compressed = state['stats']['original_tokens']
            total_without_compression = original_compressed + recent_tokens

            # Calculate real savings
            if total_without_compression > 0:
                real_savings_percent = round(
                    ((total_without_compression - actual_context_tokens) / total_without_compression) * 100, 1
                )
            else:
                real_savings_percent = 0

            return jsonify({
                'success': True,
                'stats': {
                    'total_messages': state['total_messages'],
                    'summaries_count': len(state['summaries']),
                    'recent_messages_count': len(state['recent_messages']),
                    'summaries': state['summaries'],
                    'original_tokens': state['stats']['original_tokens'],
                    'compressed_tokens': state['stats']['compressed_tokens'],
                    'savings_percent': state['stats']['savings_percent'],
                    'savings_tokens': state['stats']['original_tokens'] - state['stats']['compressed_tokens'],
                    # Real stats including recent messages
                    'summaries_tokens': summaries_tokens,
                    'recent_tokens': recent_tokens,
                    'actual_context_tokens': actual_context_tokens,
                    'total_without_compression': total_without_compression,
                    'real_savings_percent': real_savings_percent,
                    'real_savings_tokens': total_without_compression - actual_context_tokens
                }
            })
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return jsonify({'error': 'Failed to get stats', 'success': False}), 500

    # ============================================================================
    # MCP Integration Routes
    # ============================================================================

    @app.route('/api/mcp/status', methods=['GET'])
    def get_mcp_status():
        """Get MCP connection status"""
        try:
            status = mcp_client.get_status()
            return jsonify({
                'success': True,
                'status': status
            })
        except Exception as e:
            logger.error(f"Error getting MCP status: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/api/mcp/tools', methods=['GET'])
    def get_mcp_tools():
        """Get available MCP tools"""
        try:
            tools = mcp_client.get_available_tools()
            return jsonify({
                'success': True,
                'tools': tools
            })
        except Exception as e:
            logger.error(f"Error getting MCP tools: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/api/mcp/call', methods=['POST'])
    @limiter.limit("20 per minute")
    def call_mcp_tool():
        """Call an MCP tool"""
        try:
            data = request.get_json()

            if not data:
                return jsonify({'error': 'Missing request data', 'success': False}), 400

            server_name = data.get('server_name')
            tool_name = data.get('tool_name')
            arguments = data.get('arguments', {})

            if not server_name or not tool_name:
                return jsonify({'error': 'Missing server_name or tool_name', 'success': False}), 400

            # Call the tool
            result = mcp_client.call_tool(server_name, tool_name, arguments)

            return jsonify({
                'success': result.get('success', False),
                'result': result
            })
        except Exception as e:
            logger.error(f"Error calling MCP tool: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500

    # ============================================================================
    # Pipeline Agent Routes
    # ============================================================================

    @app.route('/api/pipeline/execute', methods=['POST'])
    @limiter.limit("5 per minute")  # Lower limit for complex pipeline operations
    def execute_pipeline():
        """Execute autonomous MCP pipeline"""
        try:
            data = request.get_json()

            if not data:
                return jsonify({'error': 'Missing request data', 'success': False}), 400

            query = data.get('query', '').strip()
            temperature = data.get('temperature', OPENAI_TEMPERATURE)

            if not query:
                return jsonify({'error': 'Query is required', 'success': False}), 400

            if len(query) > MAX_MESSAGE_LENGTH:
                return jsonify({'error': f'Query too long (max {MAX_MESSAGE_LENGTH})', 'success': False}), 400

            # Validate temperature
            try:
                temperature = float(temperature)
                if not 0 <= temperature <= 2:
                    return jsonify({'error': 'Temperature must be 0-2', 'success': False}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid temperature', 'success': False}), 400

            # Get pipeline agent
            agent = get_pipeline_agent()
            if not agent:
                return jsonify({'error': 'Pipeline agent not initialized', 'success': False}), 500

            # Execute pipeline
            logger.info(f"🚀 Executing pipeline for query: {query}")
            result = agent.execute_pipeline(query, temperature)

            return jsonify({
                'success': result.get('success', False),
                'answer': result.get('answer', ''),
                'steps': result.get('steps', []),
                'tools_used': result.get('tools_used', []),
                'total_steps': result.get('total_steps', 0),
                'errors': result.get('errors', [])
            })

        except Exception as e:
            logger.error(f"Error executing pipeline: {str(e)}", exc_info=True)
            return jsonify({'error': str(e), 'success': False}), 500

    # ============================================================================
    # Conversation Memory Routes (Day 11)
    # ============================================================================

    @app.route('/api/conversations', methods=['GET'])
    def get_conversations():
        """Get all conversations"""
        try:
            conversations = memory_storage.get_all_conversations()

            # Group by date
            from datetime import datetime, timedelta
            now = datetime.now()

            grouped = {
                'today': [],
                'yesterday': [],
                'last_7_days': [],
                'older': []
            }

            for conv in conversations:
                try:
                    last_updated = datetime.fromisoformat(conv['last_updated'])
                    days_ago = (now - last_updated).days

                    if days_ago == 0:
                        grouped['today'].append(conv)
                    elif days_ago == 1:
                        grouped['yesterday'].append(conv)
                    elif days_ago <= 7:
                        grouped['last_7_days'].append(conv)
                    else:
                        grouped['older'].append(conv)
                except Exception as e:
                    logger.error(f"Error grouping conversation: {e}")
                    grouped['older'].append(conv)

            return jsonify({
                'success': True,
                'conversations': grouped
            })
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/api/conversations/<int:conv_id>', methods=['GET'])
    def get_conversation(conv_id):
        """Get specific conversation with messages"""
        try:
            messages = memory_storage.load_conversation_messages(conv_id)

            return jsonify({
                'success': True,
                'conversation_id': conv_id,
                'messages': messages
            })
        except Exception as e:
            logger.error(f"Error loading conversation {conv_id}: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/api/conversations', methods=['POST'])
    def create_conversation():
        """Create new conversation"""
        try:
            conv_id = memory_storage.create_conversation()

            # Clear current session state for new conversation
            session['conversation_state'] = {
                'summaries': [],
                'recent_messages': [],
                'total_messages': 0,
                'stats': {
                    'original_tokens': 0,
                    'compressed_tokens': 0,
                    'savings_percent': 0
                }
            }
            session.modified = True

            return jsonify({
                'success': True,
                'conversation_id': conv_id
            })
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/api/conversations/<int:conv_id>', methods=['PATCH'])
    def update_conversation(conv_id):
        """Update conversation (rename)"""
        try:
            data = request.get_json()
            new_title = data.get('title', '').strip()

            if not new_title:
                return jsonify({'error': 'Title is required', 'success': False}), 400

            memory_storage.update_conversation_title(conv_id, new_title)

            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Error updating conversation {conv_id}: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/api/conversations/<int:conv_id>', methods=['DELETE'])
    def delete_conversation(conv_id):
        """Delete conversation"""
        try:
            success = memory_storage.delete_conversation(conv_id)

            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Conversation not found', 'success': False}), 404
        except Exception as e:
            logger.error(f"Error deleting conversation {conv_id}: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/api/memory/stats', methods=['GET'])
    def get_memory_stats():
        """Get memory statistics"""
        try:
            stats = memory_storage.get_stats()

            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/api/memory/export/<int:conv_id>', methods=['GET'])
    def export_conversation(conv_id):
        """Export conversation as JSON"""
        try:
            data = memory_storage.export_conversation(conv_id)

            if not data:
                return jsonify({'error': 'Conversation not found', 'success': False}), 404

            return jsonify({
                'success': True,
                'data': data
            })
        except Exception as e:
            logger.error(f"Error exporting conversation {conv_id}: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/api/memory/clear', methods=['POST'])
    def clear_all_memory():
        """Clear all memory (for testing)"""
        try:
            success = memory_storage.clear_all()

            if success:
                # Also clear session
                session['conversation_state'] = {
                    'summaries': [],
                    'recent_messages': [],
                    'total_messages': 0,
                    'stats': {
                        'original_tokens': 0,
                        'compressed_tokens': 0,
                        'savings_percent': 0
                    }
                }
                session.modified = True

                return jsonify({'success': True, 'message': 'All memory cleared'})
            else:
                return jsonify({'error': 'Failed to clear memory', 'success': False}), 500
        except Exception as e:
            logger.error(f"Error clearing memory: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500


def register_socketio_handlers(socketio):
    """
    Register all WebSocket event handlers

    Args:
        socketio: SocketIO instance
    """

    @socketio.on('connect')
    def handle_connect():
        """Handle WebSocket connection"""
        logger.info("Client connected via WebSocket")
        # Send initial MCP status
        try:
            status = mcp_client.get_status()
            emit('mcp_status', {
                'success': True,
                'status': status
            })
        except Exception as e:
            logger.error(f"Error sending initial MCP status: {str(e)}")
            emit('mcp_status', {'success': False, 'error': str(e)})

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnection"""
        logger.info("Client disconnected from WebSocket")

    @socketio.on('request_mcp_status')
    def handle_mcp_status_request():
        """Handle MCP status request via WebSocket"""
        try:
            status = mcp_client.get_status()
            emit('mcp_status', {
                'success': True,
                'status': status
            })
        except Exception as e:
            logger.error(f"Error getting MCP status: {str(e)}")
            emit('mcp_status', {'success': False, 'error': str(e)})
