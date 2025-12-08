"""
Style Cloning Routes - Day 18
API endpoints for reference image upload and style cloning
"""
import logging
import os
from datetime import datetime
from flask import request, jsonify
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Upload folder
UPLOAD_FOLDER = "reference_images"

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def register_clone_routes(app, image_style_cloner, image_generator, image_logger, csrf):
    """
    Register style cloning routes

    Args:
        app: Flask app
        image_style_cloner: ImageStyleCloner instance
        image_generator: ImageGenerator instance
        image_logger: GenerationLogger instance
        csrf: CSRF protection instance
    """

    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    @app.route('/api/clone/analyze', methods=['POST'])
    @csrf.exempt
    def analyze_reference_image():
        """
        Analyze a reference image and extract style

        Request:
            - file: Image file (multipart/form-data)

        Returns:
            JSON with style analysis
        """
        try:
            # Check if file is present
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No file uploaded'
                }), 400

            file = request.files['file']

            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'No file selected'
                }), 400

            if not allowed_file(file.filename):
                return jsonify({
                    'success': False,
                    'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
                }), 400

            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            if file_size > MAX_FILE_SIZE:
                return jsonify({
                    'success': False,
                    'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
                }), 400

            # Read file data
            image_data = file.read()
            file_ext = file.filename.rsplit('.', 1)[1].lower()

            # Analyze style
            logger.info(f"📤 Analyzing reference image: {file.filename}")
            style_analysis = image_style_cloner.analyze_image_style(image_data, file_ext)

            if not style_analysis.get('success'):
                return jsonify(style_analysis), 500

            # Save reference image for reuse
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = secure_filename(file.filename)
            saved_filename = f"{timestamp}_{safe_filename}"
            save_path = os.path.join(UPLOAD_FOLDER, saved_filename)

            with open(save_path, 'wb') as f:
                f.write(image_data)

            logger.info(f"✅ Reference image saved: {save_path}")

            # Add reference image path to response for QA visual comparison
            style_analysis['reference_image_path'] = saved_filename

            return jsonify(style_analysis)

        except Exception as e:
            logger.error(f"❌ Error analyzing reference image: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    logger.info("✅ Style cloning routes registered")
