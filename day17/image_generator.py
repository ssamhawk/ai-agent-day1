import fal_client
import os
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image
from io import BytesIO


class ImageGenerator:
    """
    Image generator using fal.ai API
    Supports multiple models with parameter control and detailed logging
    """

    SUPPORTED_MODELS = {
        "flux-pro": "fal-ai/flux-pro",
        "flux-dev": "fal-ai/flux/dev",
        "flux-schnell": "fal-ai/flux/schnell",
        "sdxl": "fal-ai/fast-sdxl",
    }

    # Pricing per image (approximate, in USD)
    MODEL_PRICING = {
        "flux-pro": 0.055,
        "flux-dev": 0.025,
        "flux-schnell": 0.003,
        "sdxl": 0.002,
    }

    def __init__(self, api_key: str):
        """Initialize the image generator with fal.ai API key"""
        os.environ["FAL_KEY"] = api_key
        self.api_key = api_key

    def generate(
        self,
        prompt: str,
        model: str = "flux-schnell",
        size: str = "landscape_4_3",
        steps: Optional[int] = None,
        seed: Optional[int] = None,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an image with specified parameters

        Args:
            prompt: Text description of the image to generate
            model: Model to use (flux-pro, flux-dev, flux-schnell, sdxl)
            size: Image size/aspect ratio
                  Options: square, square_hd, portrait_4_3, portrait_16_9,
                          landscape_4_3, landscape_16_9
            steps: Number of inference steps (quality parameter)
            seed: Random seed for reproducibility
            save_path: Path to save the generated image

        Returns:
            Dictionary with generation results and metadata
        """
        start_time = time.time()

        # Validate model
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}. Choose from {list(self.SUPPORTED_MODELS.keys())}")

        model_id = self.SUPPORTED_MODELS[model]

        # Prepare arguments
        arguments = {
            "prompt": prompt,
            "image_size": size,
        }

        # Add optional parameters
        if seed is not None:
            arguments["seed"] = seed

        if steps is not None:
            arguments["num_inference_steps"] = steps

        try:
            # Call fal.ai API
            result = fal_client.subscribe(
                model_id,
                arguments=arguments,
            )

            latency = time.time() - start_time

            # Download image
            image_url = result["images"][0]["url"]
            image_data = self._download_image(image_url)

            # Save image if path provided
            if save_path:
                os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(image_data)

            # Get image dimensions
            img = Image.open(BytesIO(image_data))
            width, height = img.size

            # Prepare response
            response = {
                "success": True,
                "model": model,
                "model_id": model_id,
                "prompt": prompt,
                "parameters": {
                    "size": size,
                    "steps": steps,
                    "seed": seed,
                    "actual_seed": result.get("seed"),
                },
                "image_url": image_url,
                "image_dimensions": {"width": width, "height": height},
                "latency_seconds": round(latency, 3),
                "cost_estimate_usd": self.MODEL_PRICING.get(model, 0.0),
                "timestamp": datetime.utcnow().isoformat(),
                "saved_path": save_path,
            }

            return response

        except Exception as e:
            latency = time.time() - start_time
            return {
                "success": False,
                "model": model,
                "model_id": model_id,
                "prompt": prompt,
                "parameters": {
                    "size": size,
                    "steps": steps,
                    "seed": seed,
                },
                "error": str(e),
                "latency_seconds": round(latency, 3),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _download_image(self, url: str) -> bytes:
        """Download image from URL"""
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content

    @staticmethod
    def get_available_models() -> Dict[str, str]:
        """Get list of available models"""
        return ImageGenerator.SUPPORTED_MODELS.copy()

    @staticmethod
    def get_model_pricing() -> Dict[str, float]:
        """Get pricing information for models"""
        return ImageGenerator.MODEL_PRICING.copy()
