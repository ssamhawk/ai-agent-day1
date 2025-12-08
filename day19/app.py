"""
Day 14 AI Application - First RAG Query
Voice-driven AI agent with RAG (Retrieval-Augmented Generation) comparison
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
import context_compression as compression
import ai_service
import speech_service
from routes import register_routes, register_socketio_handlers
from mcp_client import mcp_client
from pipeline_agent import initialize_pipeline_agent
from memory import SimpleMemoryStorage

# Import document indexing modules
from document_indexer import DocumentIndexer, EmbeddingGenerator
from vector_store import VectorStore
from indexing_routes import register_indexing_routes

# Import RAG modules
from rag_agent import RAGAgent
from rag_routes import register_rag_routes

# Import Image Generation modules
from image_generator import ImageGenerator
from logger import GenerationLogger
from image_routes import register_image_routes

# Import Style Generation modules (Day 18)
from style_manager import StyleManager
from batch_generator import BatchGenerator
from style_routes import register_style_routes

# Import Style Cloning modules (Day 18)
from image_style_cloner import ImageStyleCloner
from clone_routes import register_clone_routes

# Import QA modules (Day 19)
from image_qa_agent import ImageQAAgent

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

# Initialize Memory Storage
memory_storage = SimpleMemoryStorage(db_path="conversations.db")
logger.info("✅ Memory storage initialized")

# Configure modules with shared resources
compression.session_lock = session_lock
compression.client = client
compression.memory = memory_storage
ai_service.client = client
ai_service.memory = memory_storage
speech_service.client = client

# Initialize Pipeline Agent with memory
pipeline = initialize_pipeline_agent(client, memory_storage)

# Initialize Document Indexing
document_indexer = DocumentIndexer(
    client=client,
    chunk_size=512,
    overlap=50,
    embedding_model="text-embedding-3-small"
)
vector_store = VectorStore(
    db_path="vector_index.db",
    dimension=document_indexer.get_embedding_dimension()
)
logger.info("✅ Document indexing initialized")

# Initialize RAG Agent
rag_agent = RAGAgent(
    client=client,
    vector_store=vector_store,
    embedding_generator=document_indexer.embedding_generator,
    model=OPENAI_MODEL
)
logger.info("✅ RAG Agent initialized")

# Initialize Image Generation
fal_key = os.getenv('FAL_KEY')
if fal_key:
    image_generator = ImageGenerator(fal_key)
    image_logger = GenerationLogger(log_dir="logs/images")
    logger.info("✅ Image Generator initialized")
else:
    image_generator = None
    image_logger = None
    logger.warning("⚠️  FAL_KEY not found - image generation disabled")

# Initialize Style Generation (Day 18)
if image_generator:
    try:
        style_manager = StyleManager(profiles_path="style_profiles.json")
        batch_generator = BatchGenerator(image_generator, style_manager)
        logger.info("✅ Style Generation initialized with profiles: " + ", ".join(style_manager.list_profiles()))
    except Exception as e:
        logger.error(f"⚠️  Failed to initialize Style Generation: {str(e)}")
        style_manager = None
        batch_generator = None

    # Initialize Style Cloning (Day 18)
    try:
        image_style_cloner = ImageStyleCloner(client)
        logger.info("✅ Style Cloning initialized (Vision API)")
    except Exception as e:
        logger.error(f"⚠️  Failed to initialize Style Cloning: {str(e)}")
        image_style_cloner = None

    # Initialize Image QA Agent (Day 19)
    try:
        qa_threshold = float(os.getenv('QA_THRESHOLD', '7.0'))
        image_qa_agent = ImageQAAgent(client, default_threshold=qa_threshold)
        logger.info(f"✅ Image QA Agent initialized (threshold: {qa_threshold}/10)")
    except Exception as e:
        logger.error(f"⚠️  Failed to initialize Image QA Agent: {str(e)}")
        image_qa_agent = None
else:
    style_manager = None
    image_style_cloner = None
    batch_generator = None
    image_qa_agent = None

# Add CSP header to all responses
@app.after_request
def add_security_headers(response):
    """Add Content Security Policy and other security headers"""
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "img-src 'self' https://*.fal.media https://fonts.gstatic.com data:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "script-src 'self' 'unsafe-inline' https://cdn.socket.io; "
        "connect-src 'self' wss: ws:;"
    )
    return response

# Register routes and WebSocket handlers
register_routes(app, limiter, client, memory_storage)
register_socketio_handlers(socketio)
register_indexing_routes(app, socketio, document_indexer, vector_store, csrf)
register_rag_routes(app, rag_agent, csrf)
if image_generator and image_logger:
    register_image_routes(app, image_generator, image_logger, image_qa_agent, csrf)
if batch_generator and style_manager:
    register_style_routes(app, batch_generator, style_manager, image_logger, csrf)
if image_style_cloner and image_generator and image_logger:
    register_clone_routes(app, image_style_cloner, image_generator, image_logger, csrf)

logger.info("Application initialized successfully with modular architecture, pipeline agent, external memory, and document indexing")


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

    logger.info(f"Day 14 - First RAG Query running on http://{host}:{port}")
    print(f"Day 14 - First RAG Query running on http://{host}:{port}")
    print(f"  • Voice Agent: http://{host}:{port}/")
    print(f"  • Knowledge Base: http://{host}:{port}/rag")

    # Run with SocketIO support
    socketio.run(app, debug=debug_mode, host=host, port=port, allow_unsafe_werkzeug=True)
