import os
import logging
import json
import re
from flask import Flask, render_template, request, jsonify, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Secret key for session management - MUST be set in .env
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    logger.error("SECRET_KEY not found in environment!")
    raise ValueError("SECRET_KEY must be set in .env file for security")
app.config['SECRET_KEY'] = SECRET_KEY

# Session configuration - enhanced security
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# For production, set to True (requires HTTPS). For development, False is acceptable.
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'

# Initialize CSRF protection
csrf = CSRFProtect(app)

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

# OpenAI API constants
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.7
OPENAI_MAX_TOKENS = 800

# Field validation constants
ALLOWED_STANDARD_FIELDS = {
    'answer', 'category', 'key_points', 'confidence',
    'sources', 'related_topics'
}
MAX_CUSTOM_FIELDS = 10
MAX_TOTAL_FIELDS = 15
MAX_FIELD_NAME_LENGTH = 50

# Response format prompts - Simple for Day 4 temperature comparison
RESPONSE_PROMPTS = {
    "plain": """You are a helpful AI assistant. Provide clear, concise, and accurate responses to user questions.""",

    "json": """You are a helpful AI assistant. Always respond in valid JSON format following this exact structure:
{
  "answer": "main answer here (2-3 sentences)",
  "category": "category name (e.g., science, history, programming, general)",
  "key_points": ["point 1", "point 2", "point 3"]
}

IMPORTANT: Return ONLY the JSON object, no additional text, no markdown code blocks, no explanations.

Example:
User: "What is Python?"
Response: {"answer": "Python is a high-level, interpreted programming language known for its simplicity and readability.", "category": "programming", "key_points": ["Easy to learn syntax", "Versatile applications", "Large ecosystem"]}""",

    "markdown": """You are a helpful AI assistant. Format all responses using this exact structured markdown format:

## Answer
[Main answer in 2-3 sentences]

## Details
[More detailed explanation in 2-4 sentences]

## Key Points
- [Point 1]
- [Point 2]
- [Point 3]

## Category
**Category:** [category name]

Example:
User: "What is Python?"

## Answer
Python is a high-level, interpreted programming language known for its simplicity and readability.

## Details
Created by Guido van Rossum in 1991, Python emphasizes code readability and allows programmers to express concepts in fewer lines of code. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.

## Key Points
- Easy to learn with clean, readable syntax
- Versatile for web development, data science, AI, and automation
- Large standard library and active community support

## Category
**Category:** Programming""",

    "xml": """You are a helpful AI assistant. Always respond in valid XML format following this exact structure:
<response>
  <answer>main answer here (2-3 sentences)</answer>
  <category>category name</category>
  <key_points>
    <point>point 1</point>
    <point>point 2</point>
    <point>point 3</point>
  </key_points>
</response>

IMPORTANT: Return ONLY the XML structure, no additional text, no markdown, no explanations.

Example:
User: "What is Python?"
Response: <response><answer>Python is a high-level, interpreted programming language known for its simplicity and readability.</answer><category>programming</category><key_points><point>Easy to learn syntax</point><point>Versatile applications</point><point>Large ecosystem</point></key_points></response>"""
}


def validate_fields(fields):
    """
    Validate fields list from user input

    Args:
        fields: List of field names or None

    Returns:
        bool: True if valid, False otherwise
    """
    if not fields:
        return True

    if not isinstance(fields, list):
        return False

    if len(fields) > MAX_TOTAL_FIELDS:
        return False

    # Validate each field name
    for field in fields:
        if not isinstance(field, str):
            return False
        if len(field) > MAX_FIELD_NAME_LENGTH:
            return False
        # Allow only alphanumeric and underscores, must start with letter
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', field):
            return False

    return True


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


def generate_dynamic_prompt(response_format, fields=None):
    """
    Generate a dynamic prompt based on selected fields

    Args:
        response_format (str): Desired response format (plain, json, markdown, xml)
        fields (list): List of field names to include in response

    Returns:
        str: Generated system prompt
    """
    if not fields or response_format == "plain":
        return RESPONSE_PROMPTS.get(response_format, RESPONSE_PROMPTS["plain"])

    # Build dynamic structure based on fields
    if response_format == "json":
        field_examples = []
        for field in fields:
            if field == "answer":
                field_examples.append('"answer": "main answer here (2-3 sentences)"')
            elif field == "category":
                field_examples.append('"category": "category name (e.g., science, history, programming)"')
            elif field == "key_points":
                field_examples.append('"key_points": ["point 1", "point 2", "point 3"]')
            elif field == "confidence":
                field_examples.append('"confidence": "high/medium/low"')
            elif field == "sources":
                field_examples.append('"sources": ["source 1", "source 2"]')
            elif field == "related_topics":
                field_examples.append('"related_topics": ["topic 1", "topic 2"]')
            else:
                # Custom field
                field_examples.append(f'"{field}": "relevant {field} information"')

        structure = "{\n  " + ",\n  ".join(field_examples) + "\n}"
        return f"""You are a helpful AI assistant. Always respond in valid JSON format following this exact structure:
{structure}

IMPORTANT: Return ONLY the JSON object, no additional text, no markdown code blocks, no explanations."""

    elif response_format == "markdown":
        sections = []
        for field in fields:
            if field == "answer":
                sections.append("## Answer\n[Main answer in 2-3 sentences]")
            elif field == "category":
                sections.append("## Category\n**Category:** [category name]")
            elif field == "key_points":
                sections.append("## Key Points\n- [Point 1]\n- [Point 2]\n- [Point 3]")
            elif field == "confidence":
                sections.append("## Confidence\n**Level:** [high/medium/low]")
            elif field == "sources":
                sections.append("## Sources\n- [Source 1]\n- [Source 2]")
            elif field == "related_topics":
                sections.append("## Related Topics\n- [Topic 1]\n- [Topic 2]")
            else:
                # Custom field
                field_title = field.replace("_", " ").title()
                sections.append(f"## {field_title}\n[Relevant {field} information]")

        structure = "\n\n".join(sections)
        return f"""You are a helpful AI assistant. Format all responses using this exact structured markdown format:

{structure}"""

    elif response_format == "xml":
        field_tags = []
        for field in fields:
            if field == "answer":
                field_tags.append("  <answer>main answer here (2-3 sentences)</answer>")
            elif field == "category":
                field_tags.append("  <category>category name</category>")
            elif field == "key_points":
                field_tags.append("  <key_points>\n    <point>point 1</point>\n    <point>point 2</point>\n    <point>point 3</point>\n  </key_points>")
            elif field == "confidence":
                field_tags.append("  <confidence>high/medium/low</confidence>")
            elif field == "sources":
                field_tags.append("  <sources>\n    <source>source 1</source>\n    <source>source 2</source>\n  </sources>")
            elif field == "related_topics":
                field_tags.append("  <related_topics>\n    <topic>topic 1</topic>\n    <topic>topic 2</topic>\n  </related_topics>")
            else:
                # Custom field
                field_tags.append(f"  <{field}>relevant {field} information</{field}>")

        structure = "<response>\n" + "\n".join(field_tags) + "\n</response>"
        return f"""You are a helpful AI assistant. Always respond in valid XML format following this exact structure:
{structure}

IMPORTANT: Return ONLY the XML structure, no additional text, no markdown, no explanations."""

    return RESPONSE_PROMPTS.get(response_format, RESPONSE_PROMPTS["plain"])


def get_ai_response(user_message, response_format="plain", fields=None, temperature=OPENAI_TEMPERATURE):
    """
    Get a response from OpenAI API with conversation context

    Args:
        user_message (str): User's message
        response_format (str): Desired response format (plain, json, markdown, xml)
        fields (list): List of field names to include in structured response
        temperature (float): Temperature for response generation (0-2)

    Returns:
        str: AI agent's response
    """
    try:
        # Get the appropriate system prompt for the format
        system_prompt = generate_dynamic_prompt(response_format, fields)

        # Build messages WITHOUT conversation history for Day 4 (clean comparison)
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ]

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=temperature,  # Use the temperature parameter
            max_tokens=OPENAI_MAX_TOKENS
        )

        ai_response = response.choices[0].message.content

        # No conversation history for Day 4 - each request is independent for temperature comparison

        return ai_response

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}", exc_info=True)
        # More specific error message for user
        error_msg = "Failed to get AI response. Please try again later."
        if "rate_limit" in str(e).lower():
            error_msg = "Rate limit exceeded. Please try again in a few moments."
        elif "timeout" in str(e).lower():
            error_msg = "Request timeout. Please try again."
        elif "authentication" in str(e).lower():
            error_msg = "API authentication failed."
        raise Exception(error_msg)


def clean_json_response(response):
    """
    Clean JSON response by removing markdown code blocks if present

    Args:
        response (str): Raw response from AI

    Returns:
        str: Cleaned JSON string
    """
    # Remove markdown code blocks if present
    response = re.sub(r'^```json\s*', '', response.strip())
    response = re.sub(r'^```\s*', '', response.strip())
    response = re.sub(r'\s*```$', '', response.strip())
    return response.strip()


def clean_xml_response(response):
    """
    Clean XML response by removing markdown code blocks if present

    Args:
        response (str): Raw response from AI

    Returns:
        str: Cleaned XML string
    """
    # Remove markdown code blocks if present
    response = re.sub(r'^```xml\s*', '', response.strip())
    response = re.sub(r'^```\s*', '', response.strip())
    response = re.sub(r'\s*```$', '', response.strip())
    return response.strip()


@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self'; "
        "connect-src 'self';"
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


@app.route('/')
def home():
    """Main page with Web UI"""
    return render_template('index.html')


@app.route('/api/csrf-token', methods=['GET'])
def get_csrf_token():
    """Get CSRF token for AJAX requests"""
    from flask_wtf.csrf import generate_csrf
    return jsonify({'csrf_token': generate_csrf()})


@app.route('/api/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    """
    API endpoint for handling chat requests

    Expects JSON: {"message": "user question", "format": "plain|json|markdown|xml", "fields": ["answer", "category", ...]}
    Returns JSON: {"response": "AI response", "format": "format_used"} or {"error": "error message"}
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
        temperature = data.get('temperature', OPENAI_TEMPERATURE)  # Get temperature from request

        # Validate temperature
        try:
            temperature = float(temperature)
            if temperature < 0 or temperature > 2:
                return jsonify({
                    'error': 'Temperature must be between 0 and 2',
                    'success': False
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Temperature must be a valid number',
                'success': False
            }), 400

        response_format = 'plain'  # Day 4 only uses plain format

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

        # Get AI response with specified temperature
        ai_response = get_ai_response(user_message, response_format, None, temperature)

        # Validate JSON/XML responses can be parsed
        parsed_data = None
        if response_format == "json":
            try:
                parsed_data = json.loads(ai_response)
            except json.JSONDecodeError as e:
                logger.warning(f"AI returned invalid JSON: {e}")
                # Return raw response anyway, frontend will handle it

        return jsonify({
            'response': ai_response,
            'format': response_format,
            'parsed': parsed_data,  # Only populated for JSON format
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
    port = int(os.getenv('FLASK_PORT', 5004))

    logger.info(f"AI Agent running on http://{host}:{port}")
    print(f"AI Agent running on http://{host}:{port}")
    print(f"Debug mode: {debug_mode}")

    app.run(debug=debug_mode, host=host, port=port)
