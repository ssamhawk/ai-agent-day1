"""
Image generation routes for Day 17
"""
import os
import logging
from datetime import datetime
from flask import jsonify, request, send_file
from flask_wtf.csrf import CSRFProtect

logger = logging.getLogger(__name__)


def register_image_routes(app, image_generator, image_logger, csrf):
    """
    Register image generation routes

    Args:
        app: Flask application
        image_generator: ImageGenerator instance
        image_logger: GenerationLogger instance
        csrf: CSRF protection instance
    """

    # Ensure generated_images directory exists
    os.makedirs("generated_images", exist_ok=True)

    @app.route('/api/image/generate', methods=['POST'])
    @csrf.exempt  # Exempt for API endpoint
    def generate_image():
        """Generate an image with specified parameters"""
        if not image_generator:
            return jsonify({
                "success": False,
                "error": "Image generation not configured. FAL_KEY missing."
            }), 503

        try:
            data = request.get_json()

            # Validate required fields
            if not data or "prompt" not in data:
                return jsonify({
                    "success": False,
                    "error": "Missing required field: prompt"
                }), 400

            prompt = data["prompt"]
            model = data.get("model", "flux-schnell")
            size = data.get("size", "landscape_4_3")
            steps = data.get("steps")
            seed = data.get("seed")

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:30])
            filename = f"{timestamp}_{safe_prompt}.png"
            save_path = os.path.join("generated_images", filename)

            # Generate image
            result = image_generator.generate(
                prompt=prompt,
                model=model,
                size=size,
                steps=steps,
                seed=seed,
                save_path=save_path
            )

            # Log the request
            image_logger.log_generation(result)

            # Return response
            if result["success"]:
                return jsonify({
                    "success": True,
                    "message": "Image generated successfully",
                    "data": result
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "message": "Image generation failed",
                    "error": result.get("error"),
                    "data": result
                }), 500

        except Exception as e:
            logger.error(f"Error in generate_image: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    @app.route('/api/image/models', methods=['GET'])
    def list_models():
        """List available models and pricing"""
        if not image_generator:
            return jsonify({
                "success": False,
                "error": "Image generation not configured"
            }), 503

        return jsonify({
            "success": True,
            "models": image_generator.get_available_models(),
            "pricing_usd": image_generator.get_model_pricing()
        })


    @app.route('/api/image/stats', methods=['GET'])
    def get_stats():
        """Get aggregated statistics from all generations"""
        if not image_logger:
            return jsonify({
                "success": False,
                "error": "Image logging not configured"
            }), 503

        stats = image_logger.get_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })


    @app.route('/api/image/logs', methods=['GET'])
    def get_logs():
        """Get recent generation logs"""
        if not image_logger:
            return jsonify({
                "success": False,
                "error": "Image logging not configured"
            }), 503

        limit = request.args.get("limit", default=10, type=int)
        logs = image_logger.get_recent_logs(limit=limit)

        return jsonify({
            "success": True,
            "count": len(logs),
            "logs": logs
        })


    @app.route('/api/image/<filename>', methods=['GET'])
    def get_image(filename):
        """Serve a generated image"""
        image_path = os.path.join("generated_images", filename)
        if os.path.exists(image_path):
            return send_file(image_path, mimetype="image/png")
        else:
            return jsonify({
                "success": False,
                "error": "Image not found"
            }), 404


    logger.info("✅ Image generation routes registered")
