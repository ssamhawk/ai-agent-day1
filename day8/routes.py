"""
Routes module for Day 8 AI Application
Handles all HTTP routes and WebSocket event handlers
"""
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

# Module logger
logger = logging.getLogger(__name__)


def register_routes(app, limiter):
    """
    Register all Flask routes with the app

    Args:
        app: Flask application instance
        limiter: Flask-Limiter instance
    """

    @app.after_request
    def set_security_headers(response):
        """Add security headers"""
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' https://cdn.socket.io; "
            "connect-src 'self' ws://127.0.0.1:5008 ws://localhost:5008;"
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
