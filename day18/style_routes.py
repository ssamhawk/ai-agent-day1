"""
Style-based generation routes for Day 18
"""
import os
import logging
from flask import jsonify, request

logger = logging.getLogger(__name__)


def register_style_routes(app, batch_generator, style_manager, image_logger, csrf):
    """
    Register style-based image generation routes

    Args:
        app: Flask application
        batch_generator: BatchGenerator instance
        style_manager: StyleManager instance
        image_logger: GenerationLogger instance
        csrf: CSRF protection instance
    """

    @app.route('/api/style/profiles', methods=['GET'])
    def list_style_profiles():
        """List all available style profiles"""
        try:
            profile_names = style_manager.list_profiles()
            profiles_info = {}

            for name in profile_names:
                profiles_info[name] = style_manager.get_profile_info(name)

            return jsonify({
                "success": True,
                "count": len(profile_names),
                "profiles": profiles_info
            })

        except Exception as e:
            logger.error(f"Error listing profiles: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    @app.route('/api/style/profile/<profile_name>', methods=['GET'])
    def get_style_profile(profile_name):
        """Get detailed information about a specific profile"""
        try:
            profile = style_manager.get_profile(profile_name)

            return jsonify({
                "success": True,
                "profile": profile
            })

        except ValueError as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 404
        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    @app.route('/api/style/generate', methods=['POST'])
    @csrf.exempt
    def generate_with_style():
        """Generate single image with style profile"""
        try:
            data = request.get_json()

            # Validate required fields
            if not data or "subject" not in data or "profile" not in data:
                return jsonify({
                    "success": False,
                    "error": "Missing required fields: subject, profile"
                }), 400

            subject = data["subject"]
            profile_name = data["profile"]
            variant = data.get("variant", 0)
            additional_details = data.get("additional_details")
            model = data.get("model")
            size = data.get("size")

            # Generate single variant
            result = batch_generator.generate_variant(
                subject=subject,
                profile_name=profile_name,
                variant=variant,
                additional_details=additional_details,
                model=model,
                size=size
            )

            # Log the generation
            if image_logger:
                image_logger.log_generation(result)

            return jsonify({
                "success": result["success"],
                "data": result
            }), 200 if result["success"] else 500

        except ValueError as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 404
        except Exception as e:
            logger.error(f"Error in generate_with_style: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    @app.route('/api/style/batch', methods=['POST'])
    @csrf.exempt
    def generate_batch():
        """Generate multiple variants with style profile"""
        try:
            data = request.get_json()

            # Validate required fields
            if not data or "subject" not in data or "profile" not in data:
                return jsonify({
                    "success": False,
                    "error": "Missing required fields: subject, profile"
                }), 400

            subject = data["subject"]
            profile_name = data["profile"]
            num_variants = data.get("num_variants", 3)
            additional_details = data.get("additional_details")
            model = data.get("model")
            size = data.get("size")

            # Validate num_variants
            if not isinstance(num_variants, int) or num_variants < 1 or num_variants > 10:
                return jsonify({
                    "success": False,
                    "error": "num_variants must be between 1 and 10"
                }), 400

            # Generate batch
            result = batch_generator.generate_batch(
                subject=subject,
                profile_name=profile_name,
                num_variants=num_variants,
                additional_details=additional_details,
                model=model,
                size=size
            )

            # Log successful generations
            if image_logger:
                for gen_result in result["results"]:
                    if gen_result.get("success"):
                        image_logger.log_generation(gen_result)

            return jsonify({
                "success": result["success"],
                "data": result
            }), 200 if result["success"] else 500

        except ValueError as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 404
        except Exception as e:
            logger.error(f"Error in generate_batch: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    @app.route('/api/style/compare', methods=['POST'])
    @csrf.exempt
    def compare_styles():
        """Generate same subject across multiple styles for comparison"""
        try:
            data = request.get_json()

            # Validate required fields
            if not data or "subject" not in data:
                return jsonify({
                    "success": False,
                    "error": "Missing required field: subject"
                }), 400

            subject = data["subject"]
            profile_names = data.get("profiles")  # None = all profiles
            variants_per_style = data.get("variants_per_style", 2)
            model = data.get("model")

            # Validate variants_per_style
            if not isinstance(variants_per_style, int) or variants_per_style < 1 or variants_per_style > 5:
                return jsonify({
                    "success": False,
                    "error": "variants_per_style must be between 1 and 5"
                }), 400

            # Generate comparison
            result = batch_generator.compare_styles(
                subject=subject,
                profile_names=profile_names,
                variants_per_style=variants_per_style,
                model=model
            )

            # Log successful generations
            if image_logger:
                for profile_name, batch_result in result["styles"].items():
                    for gen_result in batch_result["results"]:
                        if gen_result.get("success"):
                            image_logger.log_generation(gen_result)

            return jsonify({
                "success": result["success"],
                "data": result
            }), 200 if result["success"] else 500

        except Exception as e:
            logger.error(f"Error in compare_styles: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    @app.route('/api/style/grid', methods=['POST'])
    @csrf.exempt
    def generate_grid():
        """Generate multiple subjects in same style"""
        try:
            data = request.get_json()

            # Validate required fields
            if not data or "subjects" not in data or "profile" not in data:
                return jsonify({
                    "success": False,
                    "error": "Missing required fields: subjects (array), profile"
                }), 400

            subjects = data["subjects"]
            profile_name = data["profile"]
            model = data.get("model")

            # Validate subjects
            if not isinstance(subjects, list) or len(subjects) == 0 or len(subjects) > 10:
                return jsonify({
                    "success": False,
                    "error": "subjects must be an array with 1-10 items"
                }), 400

            # Generate grid
            result = batch_generator.generate_grid(
                subjects=subjects,
                profile_name=profile_name,
                model=model
            )

            # Log successful generations
            if image_logger:
                for gen_result in result["results"]:
                    if gen_result.get("success"):
                        image_logger.log_generation(gen_result)

            return jsonify({
                "success": result["success"],
                "data": result
            }), 200 if result["success"] else 500

        except ValueError as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 404
        except Exception as e:
            logger.error(f"Error in generate_grid: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    logger.info("✅ Style generation routes registered")
