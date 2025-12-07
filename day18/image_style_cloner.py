"""
Image Style Cloner - Day 18
Extracts visual style from reference images using Vision API
"""
import logging
import base64
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class ImageStyleCloner:
    """
    Analyzes reference images and extracts style descriptions
    for use in image generation prompts
    """

    def __init__(self, openai_client: OpenAI):
        """
        Initialize ImageStyleCloner

        Args:
            openai_client: OpenAI client instance
        """
        self.client = openai_client
        logger.info("✅ ImageStyleCloner initialized")

    def analyze_image_style(self, image_data: bytes, image_format: str = "png") -> Dict[str, Any]:
        """
        Analyze an image and extract detailed style description

        Args:
            image_data: Image binary data
            image_format: Image format (png, jpg, jpeg, etc.)

        Returns:
            Dict containing style analysis with keys:
                - style_description: Detailed style prompt
                - color_palette: Dominant colors
                - mood: Overall mood/atmosphere
                - composition: Layout and composition notes
                - lighting: Lighting characteristics
                - texture: Texture and material notes
                - success: Boolean indicating success
        """
        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            image_url = f"data:image/{image_format};base64,{base64_image}"

            # Vision API prompt for style extraction
            system_prompt = """You are a professional art director and visual designer.
Analyze the provided image and extract comprehensive style information that can be used
to generate similar images. Focus on visual style, NOT the subject matter."""

            user_prompt = """Analyze this image and provide both subject and style description in JSON format:

{
    "subject_description": "detailed description of WHAT is in the image (objects, people, actions, setting) - 50-100 chars",
    "color_palette": ["list of dominant colors with hex codes or names"],
    "mood": "overall mood/atmosphere (e.g., energetic, calm, dramatic, playful)",
    "visual_style": "art style description (e.g., 3D render, photorealistic, minimalist, vintage)",
    "composition": "layout and composition notes (e.g., centered, rule of thirds, symmetrical)",
    "lighting": "lighting characteristics (e.g., soft natural light, dramatic shadows, bright)",
    "texture": "texture and material notes (e.g., smooth, glossy, matte, organic)",
    "level_of_detail": "low, medium, or high",
    "camera_style": "camera angle and perspective (e.g., close-up, wide angle, bird's eye)",
    "style_prompt": "complete style description WITHOUT subject (200-300 chars)"
}

IMPORTANT:
- subject_description: Describe WHAT is in the image (people, objects, actions, scene)
- style_prompt: Describe ONLY HOW it looks (style, colors, lighting, composition) - should work with ANY subject"""

            # Call Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )

            # Parse response
            import json
            style_data = json.loads(response.choices[0].message.content)

            logger.info(f"✅ Style extracted successfully")
            logger.info(f"   Subject: {style_data.get('subject_description', 'N/A')}")
            logger.info(f"   Mood: {style_data.get('mood', 'N/A')}")
            logger.info(f"   Visual style: {style_data.get('visual_style', 'N/A')}")

            return {
                **style_data,
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Failed to analyze image style: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "style_prompt": ""
            }

    def build_styled_prompt(self, subject: str, style_analysis: Dict[str, Any]) -> str:
        """
        Build a complete prompt combining subject with extracted style

        Args:
            subject: Subject to generate (e.g., "a car", "a person")
            style_analysis: Style data from analyze_image_style()

        Returns:
            Complete styled prompt
        """
        if not style_analysis.get("success"):
            logger.warning("⚠️  Style analysis failed, using plain subject")
            return subject

        style_prompt = style_analysis.get("style_prompt", "")

        if not style_prompt:
            logger.warning("⚠️  No style_prompt found, using plain subject")
            return subject

        # Combine subject with style
        full_prompt = f"{subject}, {style_prompt}"

        logger.info(f"🎨 Built styled prompt from reference image")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   Styled: {full_prompt}")

        return full_prompt
