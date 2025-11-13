import os
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Secret key for session management
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())

# Session configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_MESSAGE_LENGTH = 2000
MAX_CONVERSATION_HISTORY = 10


def get_conversation_history():
    """
    Get conversation history from session

    Returns:
        list: Conversation history
    """
    if 'conversation' not in session:
        session['conversation'] = []
    return session['conversation']


def add_to_conversation(role, content):
    """
    Add message to conversation history

    Args:
        role (str): Message role ('user' or 'assistant')
        content (str): Message content
    """
    conversation = get_conversation_history()
    conversation.append({"role": role, "content": content})

    # Keep only last MAX_CONVERSATION_HISTORY messages
    if len(conversation) > MAX_CONVERSATION_HISTORY:
        conversation = conversation[-MAX_CONVERSATION_HISTORY:]

    session['conversation'] = conversation
    session.modified = True


def get_ai_response(user_message):
    """
    Get a response from OpenAI API with conversation context

    Args:
        user_message (str): User's message

    Returns:
        str: AI agent's response
    """
    try:
        # Build messages with conversation history
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Answer questions clearly and concisely."
            }
        ]

        # Add conversation history
        conversation = get_conversation_history()
        messages.extend(conversation)

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        ai_response = response.choices[0].message.content

        # Save to conversation history
        add_to_conversation("user", user_message)
        add_to_conversation("assistant", ai_response)

        return ai_response

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise Exception("Failed to get AI response")


@app.route('/')
def home():
    """Main page with Web UI"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    """
    API endpoint for handling chat requests

    Expects JSON: {"message": "user question"}
    Returns JSON: {"response": "AI response"} or {"error": "error message"}
    """
    try:
        # Get data from request
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({
                'error': 'Missing "message" field in request',
                'success': False
            }), 400

        user_message = data['message'].strip()

        # Validate message
        if not user_message:
            return jsonify({
                'error': 'Message cannot be empty',
                'success': False
            }), 400

        if len(user_message) > MAX_MESSAGE_LENGTH:
            return jsonify({
                'error': f'Message is too long. Maximum length is {MAX_MESSAGE_LENGTH} characters',
                'success': False
            }), 400

        # Get AI response
        ai_response = get_ai_response(user_message)

        return jsonify({
            'response': ai_response,
            'success': True
        })

    except Exception as e:
        # Log the full error but don't expose it to user
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'An error occurred while processing your request. Please try again later.',
            'success': False
        }), 500


@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    """
    Clear conversation history
    """
    try:
        session['conversation'] = []
        session.modified = True
        return jsonify({
            'success': True,
            'message': 'Conversation history cleared'
        })
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        return jsonify({
            'error': 'Failed to clear conversation',
            'success': False
        }), 500


if __name__ == '__main__':
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("OpenAI API key not found!")
        print("ERROR: OpenAI API key not found!")
        print("Please add OPENAI_API_KEY to .env file")
        exit(1)

    # Get configuration from environment
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5001))

    logger.info(f"AI Agent running on http://{host}:{port}")
    print(f"AI Agent running on http://{host}:{port}")
    print(f"Debug mode: {debug_mode}")

    app.run(debug=debug_mode, host=host, port=port)
