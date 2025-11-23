import os
import logging
import json
import re
import threading
from threading import Lock
from typing import Dict, List, Any, Tuple, Optional
from flask import Flask, render_template, request, jsonify, session, Response
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken
from mcp_client import mcp_client

# Global lock for session state synchronization
session_lock = Lock()

# Load environment variables
load_dotenv()

# Configure logging FIRST (before any usage)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://"
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Constants
MAX_MESSAGE_LENGTH = 2000
DEFAULT_COMPRESSION_THRESHOLD = 10  # Compress after 10 messages
DEFAULT_RECENT_KEEP = 2  # Keep last 2 messages uncompressed

# OpenAI API constants
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.7
OPENAI_MAX_TOKENS = 1024
MODEL_CONTEXT_LIMIT = 128000

# Compression system prompt
COMPRESSION_SYSTEM_PROMPT = """You are an expert conversation compressor. Create ultra-concise summaries that preserve all essential context.

Rules:
- Extract ONLY critical facts, entities, and context needed for continuity
- Remove pleasantries, filler, and redundant information
- Use compact phrasing: "User asked about X. Discussed Y, Z."
- Maximum brevity while maintaining conversation continuity
- Target: 1-2 sentences per exchange"""

# Initialize tiktoken encoder for token counting
try:
    encoding = tiktoken.encoding_for_model(OPENAI_MODEL)
except KeyError:
    encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in text"""
    return len(encoding.encode(text))


def count_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    """Count tokens for message list"""
    tokens = 0
    for message in messages:
        tokens += 4  # Message overhead
        tokens += count_tokens(message.get('content', ''))
    tokens += 2
    return tokens


def get_conversation_state() -> Dict[str, Any]:
    """
    Get conversation state from session

    Returns:
        dict: Conversation state with summaries and recent messages
    """
    if 'conversation_state' not in session:
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
    return session['conversation_state']


def compress_messages(messages, threshold):
    """
    Compress a batch of messages into a summary

    Args:
        messages (list): Messages to compress
        threshold (int): Number of messages to compress

    Returns:
        str: Summary of the messages
    """
    try:
        # Adaptive max_tokens based on number of messages - more aggressive
        num_messages = len(messages)
        if num_messages <= 4:
            max_tokens = 60  # Short: ultra-compact
        elif num_messages <= 10:
            max_tokens = 80  # Medium: very brief
        else:
            max_tokens = 100  # Long: still concise

        # Build conversation text
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in messages
        ])

        compress_prompt = f"""Compress to essential facts only:

{conversation_text}

Output: Single compact sentence listing key topics/facts discussed."""

        messages_to_send = [
            {"role": "system", "content": COMPRESSION_SYSTEM_PROMPT},
            {"role": "user", "content": compress_prompt}
        ]

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages_to_send,
            temperature=0.3,  # Lower temperature for consistent summaries
            max_tokens=max_tokens
        )

        summary = response.choices[0].message.content
        logger.info(f"Compressed {len(messages)} messages into summary ({max_tokens} max tokens)")
        return summary

    except Exception as e:
        logger.error(f"Error compressing messages: {str(e)}")
        # Fallback: create simple summary
        return f"Discussion covering {len(messages)} messages about various topics."


def should_compress(state, threshold):
    """Check if compression should be triggered"""
    return len(state['recent_messages']) >= threshold


def compress_summaries(state):
    """
    Compress multiple summaries into one when there are too many

    Args:
        state (dict): Conversation state
    """
    try:
        # Join all summaries
        all_summaries = "\n\n".join([
            f"Summary {i+1}: {summary}"
            for i, summary in enumerate(state['summaries'])
        ])

        compress_prompt = f"""Merge these summaries into ONE ultra-compact summary:

{all_summaries}

Output: Single sentence with all critical facts."""

        messages_to_send = [
            {"role": "system", "content": COMPRESSION_SYSTEM_PROMPT},
            {"role": "user", "content": compress_prompt}
        ]

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages_to_send,
            temperature=0.3,
            max_tokens=60  # Very aggressive compression
        )

        combined_summary = response.choices[0].message.content

        # Calculate token changes
        old_tokens = sum(count_tokens(s) for s in state['summaries'])
        new_tokens = count_tokens(combined_summary)

        # Update stats - we're re-compressing, so adjust the compressed tokens
        state['stats']['compressed_tokens'] = state['stats']['compressed_tokens'] - old_tokens + new_tokens

        # Replace all summaries with the combined one
        state['summaries'] = [combined_summary]

        logger.info(f"Compressed {len(state['summaries'])} summaries: {old_tokens} → {new_tokens} tokens")

    except Exception as e:
        logger.error(f"Error compressing summaries: {str(e)}")


def perform_compression(state, threshold, keep_recent):
    """
    Perform compression on conversation state with thread safety

    Args:
        state (dict): Current conversation state
        threshold (int): Compression threshold
        keep_recent (int): Number of recent messages to keep
    """
    with session_lock:
        recent = state['recent_messages']

        if len(recent) < threshold:
            return  # Not enough messages to compress

        # Messages to compress
        to_compress = recent[:-keep_recent] if keep_recent > 0 else recent
        # Messages to keep
        to_keep = recent[-keep_recent:] if keep_recent > 0 else []

        if not to_compress:
            return

        # Calculate original tokens
        original_tokens = count_messages_tokens(to_compress)

        # Create summary
        summary = compress_messages(to_compress, threshold)
        summary_tokens = count_tokens(summary)

        # Update state
        state['summaries'].append(summary)
        state['recent_messages'] = to_keep

        # Update stats
        state['stats']['original_tokens'] += original_tokens
        state['stats']['compressed_tokens'] += summary_tokens

        # Calculate savings
        total_original = state['stats']['original_tokens']
        total_compressed = state['stats']['compressed_tokens']
        if total_original > 0:
            state['stats']['savings_percent'] = round(
                ((total_original - total_compressed) / total_original) * 100, 1
            )

        # Compress summaries if too many (recursive compression)
        MAX_SUMMARIES = 3
        if len(state['summaries']) > MAX_SUMMARIES:
            compress_summaries(state)

        session.modified = True
        logger.info(f"Compression: {original_tokens} → {summary_tokens} tokens ({state['stats']['savings_percent']}% savings)")


def build_context(state):
    """
    Build conversation context from compressed state

    Args:
        state (dict): Conversation state

    Returns:
        list: Messages for API (summaries + recent messages)
    """
    messages = []

    # Add summaries as system messages
    if state['summaries']:
        summaries_text = "\n\n".join([
            f"Previous conversation summary {i+1}:\n{summary}"
            for i, summary in enumerate(state['summaries'])
        ])
        messages.append({
            "role": "system",
            "content": f"Context from previous conversation:\n\n{summaries_text}"
        })

    # Add recent messages
    messages.extend(state['recent_messages'])

    return messages


def add_message_to_conversation(role, content, compression_enabled, threshold, keep_recent):
    """
    Add message to conversation with optional compression (thread-safe)

    Args:
        role (str): Message role
        content (str): Message content
        compression_enabled (bool): Whether compression is enabled
        threshold (int): Compression threshold
        keep_recent (int): Number of recent messages to keep
    """
    with session_lock:
        state = get_conversation_state()

        # Add message to recent
        state['recent_messages'].append({
            "role": role,
            "content": content
        })
        state['total_messages'] += 1

        # Check if compression needed - only compress after assistant messages
        if compression_enabled and role == "assistant" and should_compress(state, threshold):
            # Release lock temporarily for compression (it will re-acquire)
            pass

        session['conversation_state'] = state
        session.modified = True

    # Perform compression outside the lock to avoid holding it too long
    if compression_enabled and role == "assistant":
        state = get_conversation_state()
        if should_compress(state, threshold):
            perform_compression(state, threshold, keep_recent)


# Response format prompts
RESPONSE_PROMPTS = {
    "plain": """You are a helpful AI assistant. Provide clear, concise, and accurate responses to user questions.

IMPORTANT: Always respond in the SAME LANGUAGE as the user's question. If the user writes in Ukrainian, respond in Ukrainian. If in English, respond in English. Match the user's language automatically.""",

    "plain_intelligent": """You are an intelligent AI assistant with MCP (Model Context Protocol) tools for web search and filesystem access.

CORE ABILITIES:
1. **Web Search**: Search the internet using Brave Search MCP tool for current information
2. **Filesystem Access**: List and read files on the user's computer using filesystem MCP tool
3. **Intelligent Decision Making**: Know when you need more information or tools
4. **Multilingual**: Automatically detect and respond in the user's language

LANGUAGE DETECTION:
- ALWAYS respond in the SAME LANGUAGE as the user's question
- If user writes in Ukrainian → respond in Ukrainian
- If user writes in English → respond in English
- If user writes in Spanish → respond in Spanish
- Match the user's language automatically for ALL responses

DECISION LOGIC:
1. If the question requires CURRENT/RECENT information (news, weather, prices, etc.) → Use web search
2. If the question is about FILES or DIRECTORIES on their computer → Use filesystem tool
3. If the question is about GENERAL KNOWLEDGE you already have → Answer directly
4. If the question is VAGUE or MISSING KEY DETAILS → Ask clarifying questions

HOW TO USE WEB SEARCH:
When you need current information, respond with a special command:
[MCP_SEARCH: your search query here in English]

Example:
User: "Яка зараз погода у Барселоні?"
Assistant: [MCP_SEARCH: Barcelona weather today]
(Then respond in Ukrainian based on search results)

HOW TO USE FILESYSTEM:
When user asks about files or directories, use these commands:

**List Files in Directory:**
[MCP_LIST_FILES: /path/to/directory]

Examples:
User: "Покажи список файлів на робочому столі"
Assistant: [MCP_LIST_FILES: ~/Desktop]
(Then respond in Ukrainian with the file list)

User: "What files are in my Documents folder?"
Assistant: [MCP_LIST_FILES: ~/Documents]
(Then respond in English with the file list)

User: "Які файли є в директорії day8?"
Assistant: [MCP_LIST_FILES: /Users/viacheslavskrynnyk/projects/ai-challange/day8]
(Then respond in Ukrainian with the file list)

**Read File Content:**
[MCP_READ_FILE: /path/to/file.ext]

Examples:
User: "Прочитай файл .zshrc"
Assistant: [MCP_READ_FILE: ~/.zshrc]
(Then respond in Ukrainian with file content summary)

User: "Show me what's in app.py"
Assistant: [MCP_READ_FILE: app.py]
(Then respond in English with file content summary)

IMPORTANT:
- Use ~ for home directory (e.g., ~/Desktop, ~/Documents)
- Use absolute paths when possible
- Be conversational and natural
- Provide the complete final answer in the user's language after tool execution""",

    "json": """You are a helpful AI assistant. Always respond in valid JSON format following this exact structure:
{
  "answer": "main answer here (2-3 sentences)",
  "category": "category name (e.g., science, history, programming, general)",
  "key_points": ["point 1", "point 2", "point 3"]
}

IMPORTANT:
- Return ONLY the JSON object, no additional text, no markdown code blocks
- Respond in the SAME LANGUAGE as the user's question (Ukrainian → Ukrainian, English → English, etc.)
- All JSON values should be in the user's language""",

    "markdown": """You are a helpful AI assistant. Format all responses using this exact structured markdown format:

## Answer
[Main answer in 2-3 sentences]

## Details
[More detailed explanation]

## Key Points
- [Point 1]
- [Point 2]
- [Point 3]

## Category
**Category:** [category name]

IMPORTANT: Respond in the SAME LANGUAGE as the user's question (Ukrainian → Ukrainian, English → English, etc.)""",

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

IMPORTANT:
- Return ONLY the XML structure, no additional text
- Respond in the SAME LANGUAGE as the user's question (Ukrainian → Ukrainian, English → English, etc.)
- All XML values should be in the user's language"""
}


def generate_dynamic_prompt(response_format, fields=None, intelligent_mode=False):
    """Generate system prompt based on format and mode"""
    if response_format == "plain" and intelligent_mode:
        return RESPONSE_PROMPTS.get("plain_intelligent", RESPONSE_PROMPTS["plain"])

    return RESPONSE_PROMPTS.get(response_format, RESPONSE_PROMPTS["plain"])


def process_mcp_commands(text, intelligent_mode=False):
    """
    Process MCP commands in AI response (search, list files, read files)

    Args:
        text (str): AI response text
        intelligent_mode (bool): Whether intelligent mode is enabled

    Returns:
        tuple: (processed_text, used_mcp_flag)
    """
    if not intelligent_mode:
        return text, False

    import re

    used_mcp = False

    # Process MCP_SEARCH commands
    search_pattern = r'\[MCP_SEARCH:\s*([^\]]+)\]'
    search_matches = re.findall(search_pattern, text)

    if search_matches:
        used_mcp = True
        logger.info(f"Found {len(search_matches)} MCP search commands")

        for query in search_matches:
            query = query.strip()
            logger.info(f"Executing MCP search: {query}")

            try:
                result = mcp_client.call_tool(
                    server_name="brave_search",
                    tool_name="search",
                    arguments={"query": query, "max_results": 5}
                )

                if result.get("success"):
                    search_results = result.get("result", {}).get("content", "")
                    replacement = f"\n\n🔍 **Web Search Results for '{query}':**\n\n{search_results}\n"
                    text = text.replace(f"[MCP_SEARCH: {query}]", replacement)
                else:
                    error_msg = result.get("error", "Unknown error")
                    replacement = f"\n\n⚠️ Search failed for '{query}': {error_msg}\n"
                    text = text.replace(f"[MCP_SEARCH: {query}]", replacement)

            except Exception as e:
                logger.error(f"Error executing MCP search: {str(e)}")
                replacement = f"\n\n❌ Error searching for '{query}': {str(e)}\n"
                text = text.replace(f"[MCP_SEARCH: {query}]", replacement)

    # Process MCP_LIST_FILES commands
    list_pattern = r'\[MCP_LIST_FILES:\s*([^\]]+)\]'
    list_matches = re.findall(list_pattern, text)

    if list_matches:
        used_mcp = True
        logger.info(f"Found {len(list_matches)} MCP list_files commands")

        for path in list_matches:
            path = path.strip()
            logger.info(f"Executing MCP list_files: {path}")

            try:
                result = mcp_client.call_tool(
                    server_name="filesystem",
                    tool_name="list_files",
                    arguments={"path": path}
                )

                if result.get("success"):
                    file_list = result.get("result", {}).get("content", "")
                    replacement = f"\n\n📁 **Files in '{path}':**\n\n{file_list}\n"
                    text = text.replace(f"[MCP_LIST_FILES: {path}]", replacement)
                else:
                    error_msg = result.get("error", "Unknown error")
                    replacement = f"\n\n⚠️ Failed to list files in '{path}': {error_msg}\n"
                    text = text.replace(f"[MCP_LIST_FILES: {path}]", replacement)

            except Exception as e:
                logger.error(f"Error executing MCP list_files: {str(e)}")
                replacement = f"\n\n❌ Error listing files in '{path}': {str(e)}\n"
                text = text.replace(f"[MCP_LIST_FILES: {path}]", replacement)

    # Process MCP_READ_FILE commands
    read_pattern = r'\[MCP_READ_FILE:\s*([^\]]+)\]'
    read_matches = re.findall(read_pattern, text)

    if read_matches:
        used_mcp = True
        logger.info(f"Found {len(read_matches)} MCP read_file commands")

        for path in read_matches:
            path = path.strip()
            logger.info(f"Executing MCP read_file: {path}")

            try:
                result = mcp_client.call_tool(
                    server_name="filesystem",
                    tool_name="read_file",
                    arguments={"path": path}
                )

                if result.get("success"):
                    file_content = result.get("result", {}).get("content", "")
                    replacement = f"\n\n📄 **Content of '{path}':**\n\n{file_content}\n"
                    text = text.replace(f"[MCP_READ_FILE: {path}]", replacement)
                else:
                    error_msg = result.get("error", "Unknown error")
                    replacement = f"\n\n⚠️ Failed to read file '{path}': {error_msg}\n"
                    text = text.replace(f"[MCP_READ_FILE: {path}]", replacement)

            except Exception as e:
                logger.error(f"Error executing MCP read_file: {str(e)}")
                replacement = f"\n\n❌ Error reading file '{path}': {str(e)}\n"
                text = text.replace(f"[MCP_READ_FILE: {path}]", replacement)

    return text, used_mcp


def get_ai_response(user_message, response_format="plain", fields=None, temperature=OPENAI_TEMPERATURE,
                   intelligent_mode=False, max_tokens=OPENAI_MAX_TOKENS, compression_enabled=True,
                   threshold=DEFAULT_COMPRESSION_THRESHOLD, keep_recent=DEFAULT_RECENT_KEEP):
    """
    Get AI response with compression support and MCP integration

    Args:
        user_message (str): User's message
        response_format (str): Response format
        fields (list): Fields configuration
        temperature (float): Temperature
        intelligent_mode (bool): Intelligent mode (enables MCP search)
        max_tokens (int): Max tokens
        compression_enabled (bool): Enable compression
        threshold (int): Compression threshold
        keep_recent (int): Recent messages to keep

    Returns:
        dict: Response with compression stats and MCP usage info
    """
    try:
        # Get system prompt
        system_prompt = generate_dynamic_prompt(response_format, fields, intelligent_mode)

        # Get conversation state
        state = get_conversation_state()

        # Build context from compressed history
        context_messages = build_context(state)

        # Build full message list
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(context_messages)
        messages.append({"role": "user", "content": user_message})

        # Count tokens
        input_tokens = count_messages_tokens(messages)

        # Check context limit
        if input_tokens + max_tokens > MODEL_CONTEXT_LIMIT:
            available = MODEL_CONTEXT_LIMIT - input_tokens
            if available <= 0:
                raise Exception(f"Context too long ({input_tokens} tokens)")
            max_tokens = min(max_tokens, available)

        # Get initial response
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        ai_response = response.choices[0].message.content

        # Process MCP commands if in intelligent mode
        ai_response, used_mcp = process_mcp_commands(ai_response, intelligent_mode)

        # If MCP was used, do a second pass to let AI synthesize the search results
        if used_mcp:
            logger.info("MCP search completed, getting final AI synthesis...")

            # Add the search results to context and ask AI to synthesize
            messages.append({"role": "assistant", "content": ai_response})
            messages.append({"role": "user", "content": "Based on the search results above, please provide a comprehensive answer to my original question."})

            # Get final synthesized response
            final_response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            ai_response = final_response.choices[0].message.content

        # Add messages to conversation
        add_message_to_conversation("user", user_message, compression_enabled, threshold, keep_recent)
        add_message_to_conversation("assistant", ai_response, compression_enabled, threshold, keep_recent)

        # Get token usage
        output_tokens = response.usage.completion_tokens
        actual_input_tokens = response.usage.prompt_tokens
        total_tokens = response.usage.total_tokens

        # Get updated stats
        updated_state = get_conversation_state()

        # Calculate what input tokens would be without compression (for this specific request)
        # If we have summaries, calculate what the original messages would have been
        summaries_tokens = sum(count_tokens(s) for s in updated_state['summaries'])
        recent_tokens = count_messages_tokens(updated_state['recent_messages'])

        # Calculate tokens saved in this request
        tokens_saved_this_request = 0
        if compression_enabled and len(updated_state['summaries']) > 0:
            # What we're using: summaries + recent
            compressed_context = summaries_tokens + recent_tokens
            # What it would be: original compressed messages + recent
            uncompressed_context = updated_state['stats']['original_tokens'] + recent_tokens
            tokens_saved_this_request = uncompressed_context - compressed_context

        return {
            'response': ai_response,
            'tokens': {
                'input': actual_input_tokens,
                'output': output_tokens,
                'total': total_tokens,
                'max_output': max_tokens,
                'limit': MODEL_CONTEXT_LIMIT,
                'percentage': round((total_tokens / MODEL_CONTEXT_LIMIT) * 100, 2),
                'saved_this_request': tokens_saved_this_request  # New field
            },
            'compression_stats': {
                'enabled': compression_enabled,
                'total_messages': updated_state['total_messages'],
                'summaries_count': len(updated_state['summaries']),
                'recent_messages_count': len(updated_state['recent_messages']),
                'original_tokens': updated_state['stats']['original_tokens'],
                'compressed_tokens': updated_state['stats']['compressed_tokens'],
                'savings_percent': updated_state['stats']['savings_percent']
            },
            'truncated': response.choices[0].finish_reason == 'length'
        }

    except Exception as e:
        logger.error(f"Error in get_ai_response: {str(e)}", exc_info=True)
        raise


@app.after_request
def set_security_headers(response):
    """Add security headers"""
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
    """Main page"""
    return render_template('index.html')


@app.route('/api/csrf-token', methods=['GET'])
def get_csrf_token():
    """Get CSRF token"""
    from flask_wtf.csrf import generate_csrf
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


# ====================
# WebSocket Event Handlers
# ====================

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


# ====================
# MCP Initialization
# ====================

def initialize_mcp_in_background():
    """Initialize MCP client in a background thread"""
    try:
        logger.info("Starting MCP initialization in background...")
        connected_servers = mcp_client.initialize_servers()
        if connected_servers:
            logger.info(f"MCP initialized with servers: {', '.join(connected_servers)}")
            # Notify all connected clients via WebSocket
            socketio.emit('mcp_status', {
                'success': True,
                'status': mcp_client.get_status()
            })
        else:
            logger.warning("No MCP servers connected")
    except Exception as e:
        logger.error(f"Error initializing MCP: {str(e)}")


if __name__ == '__main__':
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("OpenAI API key not found!")
        print("ERROR: OpenAI API key not found!")
        exit(1)

    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5008))

    # Initialize MCP in background thread
    mcp_thread = threading.Thread(target=initialize_mcp_in_background, daemon=True)
    mcp_thread.start()

    logger.info(f"Day 8 - MCP Integration running on http://{host}:{port}")
    print(f"Day 8 - MCP Integration running on http://{host}:{port}")

    # Run with SocketIO support
    socketio.run(app, debug=debug_mode, host=host, port=port, allow_unsafe_werkzeug=True)
