"""
Day 10 AI Application - MCP Pipeline Agent
Automated MCP pipeline where tools are combined into a sequence and executed step by step
"""
import os
import logging
import threading
from threading import Lock
from flask import Flask
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from openai import OpenAI
from dotenv import load_dotenv

# Import configuration
from config import OPENAI_MODEL

# Import and configure modules
import compression
import ai_service
from routes import register_routes, register_socketio_handlers
from mcp_client import mcp_client
from pipeline_agent import initialize_pipeline_agent

# Load environment variables
load_dotenv()

# Configure logging FIRST (before any usage)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global lock for session state synchronization
session_lock = Lock()

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

# Configure modules with shared resources
compression.session_lock = session_lock
compression.client = client
ai_service.client = client

# Initialize Pipeline Agent
pipeline = initialize_pipeline_agent(client)

# Register routes and WebSocket handlers
register_routes(app, limiter, client)
register_socketio_handlers(socketio)

logger.info("Application initialized successfully with modular architecture and pipeline agent")


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
    port = int(os.getenv('FLASK_PORT', 5010))

    # Initialize MCP in background thread
    mcp_thread = threading.Thread(target=initialize_mcp_in_background, daemon=True)
    mcp_thread.start()

    logger.info(f"Day 10 - MCP Pipeline Agent running on http://{host}:{port}")
    print(f"Day 10 - MCP Pipeline Agent running on http://{host}:{port}")

    # Run with SocketIO support
    socketio.run(app, debug=debug_mode, host=host, port=port, allow_unsafe_werkzeug=True)
