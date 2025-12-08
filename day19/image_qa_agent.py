"""
Image QA Agent - Day 19
Automated quality assurance for generated images using Vision API
"""
import logging
import base64
import json
from typing import Dict, Any, Optional, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class ImageQAAgent:
    """
    Universal QA agent for evaluating generated images
    Works with both preset styles and reference images
    """

    def __init__(self, openai_client: OpenAI, default_threshold: float = 7.0):
        """
        Initialize ImageQAAgent

        Args:
            openai_client: OpenAI client instance
            default_threshold: Default passing score threshold (0-10)
        """
        self.client = openai_client
        self.default_threshold = default_threshold
        logger.info(f"✅ ImageQAAgent initialized (threshold: {default_threshold})")

    def evaluate_image(
        self,
        image_data: bytes,
        original_prompt: str,
        checklist: Optional[Dict[str, Any]] = None,
        reference_image_data: Optional[bytes] = None,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluate generated image quality against checklist

        Universal method that works with:
        1. Text-based checklist (preset styles)
        2. Visual reference image (style cloning)

        Args:
            image_data: Generated image binary data
            original_prompt: User's original prompt
            checklist: Quality checklist with expected attributes:
                {
                    "color_palette": ["#FF006E", "#00F0FF"],
                    "visual_style": "cyberpunk, neon lights",
                    "mood": "futuristic, edgy",
                    "composition": "centered, rule of thirds"
                }
            reference_image_data: Optional reference image for visual comparison
            threshold: Passing score threshold (overrides default)

        Returns:
            {
                "success": True,
                "overall_score": 8.5,
                "passed": True,
                "checks": {
                    "color_palette": {"score": 9.0, "feedback": "..."},
                    "visual_style": {"score": 8.0, "feedback": "..."},
                    "subject_match": {"score": 10.0, "feedback": "..."},
                    "quality": {"score": 7.0, "feedback": "..."}
                },
                "suggestions": "Improve sharpness...",
                "comparison_mode": "visual" or "text"
            }
        """
        try:
            threshold = threshold or self.default_threshold
            comparison_mode = "visual" if reference_image_data else "text"

            logger.info(f"🔍 Starting QA evaluation (mode: {comparison_mode})")
            logger.info(f"   Prompt: {original_prompt}")
            logger.info(f"   Threshold: {threshold}/10")

            # Build Vision API prompt
            if reference_image_data:
                qa_result = self._evaluate_with_reference(
                    image_data, original_prompt, reference_image_data, checklist
                )
            else:
                qa_result = self._evaluate_with_checklist(
                    image_data, original_prompt, checklist
                )

            # Determine if passed
            overall_score = qa_result["overall_score"]
            passed = overall_score >= threshold

            result = {
                **qa_result,
                "passed": passed,
                "threshold": threshold,
                "comparison_mode": comparison_mode
            }

            # Log results
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"{status} QA Check: {overall_score:.1f}/10 (threshold: {threshold})")

            for check_name, check_data in qa_result.get("checks", {}).items():
                score = check_data.get("score", 0)
                logger.info(f"   {check_name}: {score:.1f}/10")

            return result

        except Exception as e:
            logger.error(f"❌ QA evaluation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "overall_score": 0.0,
                "passed": False,
                "checks": {}
            }

    def _evaluate_with_reference(
        self,
        image_data: bytes,
        original_prompt: str,
        reference_image_data: bytes,
        checklist: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate by visual comparison with reference image
        Most accurate method - Vision API compares images directly
        """
        logger.info("📸 Visual comparison mode")

        # Encode both images
        generated_b64 = base64.b64encode(image_data).decode('utf-8')
        reference_b64 = base64.b64encode(reference_image_data).decode('utf-8')

        generated_url = f"data:image/png;base64,{generated_b64}"
        reference_url = f"data:image/png;base64,{reference_b64}"

        # Build comparison prompt
        system_prompt = """You are a professional image quality inspector and art director.
Compare the generated image with the reference image and evaluate style consistency.
Be strict but fair - focus on visual similarity, not exact duplication."""

        checklist_text = ""
        if checklist:
            checklist_text = f"\n\nAdditional requirements:\n"
            for key, value in checklist.items():
                if isinstance(value, list):
                    checklist_text += f"- {key}: {', '.join(str(v) for v in value)}\n"
                else:
                    checklist_text += f"- {key}: {value}\n"

        user_prompt = f"""Compare these two images:

1. REFERENCE IMAGE (style to match)
2. GENERATED IMAGE (to evaluate)

Original prompt: "{original_prompt}"
{checklist_text}

Evaluate the GENERATED image on:
1. **color_palette** (0-10): Do colors match the reference?
2. **visual_style** (0-10): Does artistic style match (3D/realistic/illustration)?
3. **mood** (0-10): Does atmosphere/mood match?
4. **composition** (0-10): Similar layout and framing?
5. **subject_match** (0-10): Does it contain what was requested in the prompt?
6. **quality** (0-10): Is it sharp, clear, no artifacts?

IMPORTANT: Calculate overall_score as weighted average with these weights:
- subject_match: 25% (important but not critical)
- quality: 20% (high quality is valuable)
- visual_style: 20% (style match is important)
- composition: 15% (good framing matters)
- color_palette: 12% (colors important for styled images)
- mood: 8% (least critical)

Formula: overall_score = subject_match*0.25 + quality*0.20 + visual_style*0.20 + composition*0.15 + color_palette*0.12 + mood*0.08

Return JSON:
{{
    "overall_score": 0.0-10.0,
    "checks": {{
        "color_palette": {{"score": 0-10, "feedback": "detailed explanation"}},
        "visual_style": {{"score": 0-10, "feedback": "..."}},
        "mood": {{"score": 0-10, "feedback": "..."}},
        "composition": {{"score": 0-10, "feedback": "..."}},
        "subject_match": {{"score": 0-10, "feedback": "..."}},
        "quality": {{"score": 0-10, "feedback": "..."}}
    }},
    "suggestions": "how to improve the generated image",
    "success": true
}}"""

        # Call Vision API with both images
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": reference_url}},
                        {"type": "image_url", "image_url": {"url": generated_url}}
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=1500
        )

        # Parse response
        result = json.loads(response.choices[0].message.content)
        logger.info(f"✅ Visual QA completed: {result.get('overall_score', 0)}/10")

        return result

    def _evaluate_with_checklist(
        self,
        image_data: bytes,
        original_prompt: str,
        checklist: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate based on text checklist (preset styles)
        Good for structured style profiles
        """
        logger.info("📋 Text-based checklist mode")

        # Encode image
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        image_url = f"data:image/png;base64,{image_b64}"

        # Build checklist text
        checklist_text = ""
        if checklist:
            for key, value in checklist.items():
                if isinstance(value, list):
                    checklist_text += f"- {key}: {', '.join(str(v) for v in value)}\n"
                else:
                    checklist_text += f"- {key}: {value}\n"
        else:
            checklist_text = "No specific checklist provided - evaluate general quality"

        system_prompt = """You are a professional image quality inspector.
Evaluate the generated image against the provided checklist.
Be strict but fair - the image should match the requirements closely."""

        user_prompt = f"""Evaluate this generated image:

Original prompt: "{original_prompt}"

Quality Checklist:
{checklist_text}

Evaluate on:
1. **color_palette** (0-10): Do colors match expected palette?
2. **visual_style** (0-10): Does artistic style match requirements?
3. **mood** (0-10): Does atmosphere match expected mood?
4. **composition** (0-10): Good framing and layout?
5. **subject_match** (0-10): Contains what was requested in prompt?
6. **quality** (0-10): Sharp, clear, no artifacts or distortions?

IMPORTANT: Calculate overall_score as weighted average with these weights:
- subject_match: 25% (important but not critical)
- quality: 20% (high quality is valuable)
- visual_style: 20% (style match is important)
- composition: 15% (good framing matters)
- color_palette: 12% (colors important for styled images)
- mood: 8% (least critical)

Formula: overall_score = subject_match*0.25 + quality*0.20 + visual_style*0.20 + composition*0.15 + color_palette*0.12 + mood*0.08

Return JSON:
{{
    "overall_score": 0.0-10.0,
    "checks": {{
        "color_palette": {{"score": 0-10, "feedback": "detailed explanation"}},
        "visual_style": {{"score": 0-10, "feedback": "..."}},
        "mood": {{"score": 0-10, "feedback": "..."}},
        "composition": {{"score": 0-10, "feedback": "..."}},
        "subject_match": {{"score": 0-10, "feedback": "..."}},
        "quality": {{"score": 0-10, "feedback": "..."}}
    }},
    "suggestions": "specific suggestions to improve",
    "success": true
}}"""

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
            max_tokens=1500
        )

        # Parse response
        result = json.loads(response.choices[0].message.content)
        logger.info(f"✅ Checklist QA completed: {result.get('overall_score', 0)}/10")

        return result

    def batch_evaluate(
        self,
        images: List[Dict[str, Any]],
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluate multiple images and return best one

        Args:
            images: List of dicts with 'image_data', 'prompt', 'checklist', etc.
            threshold: Passing threshold

        Returns:
            {
                "best_image": {...},
                "all_results": [...],
                "passed_count": 3,
                "total_count": 5
            }
        """
        threshold = threshold or self.default_threshold
        results = []

        logger.info(f"🔍 Batch evaluation: {len(images)} images")

        for idx, img_data in enumerate(images):
            logger.info(f"   Evaluating image {idx + 1}/{len(images)}")

            result = self.evaluate_image(
                image_data=img_data["image_data"],
                original_prompt=img_data["prompt"],
                checklist=img_data.get("checklist"),
                reference_image_data=img_data.get("reference_image_data"),
                threshold=threshold
            )

            results.append({
                **result,
                "index": idx,
                "metadata": img_data.get("metadata", {})
            })

        # Find best image
        passed_results = [r for r in results if r.get("passed")]
        best_result = max(results, key=lambda x: x.get("overall_score", 0))

        logger.info(f"✅ Batch complete: {len(passed_results)}/{len(images)} passed")
        logger.info(f"   Best score: {best_result.get('overall_score', 0)}/10")

        return {
            "best_image": best_result,
            "all_results": results,
            "passed_count": len(passed_results),
            "total_count": len(images),
            "success": True
        }
