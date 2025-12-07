"""
Batch Generator for Day 18 - Brand-consistent Image Generation
Orchestrates StyleManager + ImageGenerator for batch operations
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from image_generator import ImageGenerator
from style_manager import StyleManager

logger = logging.getLogger(__name__)


class BatchGenerator:
    """Generates multiple images with style consistency"""

    def __init__(self, image_generator: ImageGenerator, style_manager: StyleManager):
        """
        Initialize BatchGenerator

        Args:
            image_generator: ImageGenerator instance
            style_manager: StyleManager instance
        """
        self.image_generator = image_generator
        self.style_manager = style_manager

    def generate_variant(
        self,
        subject: str,
        profile_name: str,
        variant: int = 0,
        additional_details: Optional[str] = None,
        model: Optional[str] = None,
        size: Optional[str] = None,
        save_dir: str = "generated_images"
    ) -> Dict[str, Any]:
        """
        Generate a single variant with style profile

        Args:
            subject: Main subject to generate
            profile_name: Style profile to use
            variant: Variant number (affects seed)
            additional_details: Optional extra details
            model: Model override
            size: Size override
            save_dir: Directory to save images

        Returns:
            Generation result with metadata
        """
        # Get generation config from style manager
        config = self.style_manager.get_generation_config(
            subject=subject,
            profile_name=profile_name,
            variant=variant,
            additional_details=additional_details,
            model=model,
            size=size
        )

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_subject = "".join(c if c.isalnum() else "_" for c in subject[:20])
        filename = f"{timestamp}_{profile_name}_v{variant}_{safe_subject}.png"
        save_path = os.path.join(save_dir, filename)

        # Generate image
        result = self.image_generator.generate(
            prompt=config["prompt"],
            model=config["model"],
            size=config["size"],
            seed=config["seed"],
            save_path=save_path
        )

        # Add style metadata to result
        result["style_metadata"] = {
            "profile_name": profile_name,
            "profile_version": config["style_version"],
            "subject": subject,
            "variant": variant,
            "additional_details": additional_details
        }

        return result

    def generate_batch(
        self,
        subject: str,
        profile_name: str,
        num_variants: int = 3,
        additional_details: Optional[str] = None,
        model: Optional[str] = None,
        size: Optional[str] = None,
        save_dir: str = "generated_images"
    ) -> Dict[str, Any]:
        """
        Generate multiple variants of same subject in same style

        Args:
            subject: Main subject
            profile_name: Style profile
            num_variants: Number of variants to generate
            additional_details: Optional extra details
            model: Model override
            size: Size override
            save_dir: Directory to save images

        Returns:
            Batch results with all variants
        """
        os.makedirs(save_dir, exist_ok=True)

        results = []
        successes = 0
        failures = 0
        total_cost = 0.0
        total_time = 0.0

        logger.info(f"Starting batch generation: {num_variants} variants of '{subject}' in '{profile_name}' style")

        for variant in range(num_variants):
            try:
                result = self.generate_variant(
                    subject=subject,
                    profile_name=profile_name,
                    variant=variant,
                    additional_details=additional_details,
                    model=model,
                    size=size,
                    save_dir=save_dir
                )

                results.append(result)

                if result["success"]:
                    successes += 1
                    total_cost += result.get("cost_estimate_usd", 0.0)
                    total_time += result.get("latency_seconds", 0.0)
                else:
                    failures += 1

                logger.info(f"Variant {variant}/{num_variants-1}: {'✅ Success' if result['success'] else '❌ Failed'}")

            except Exception as e:
                logger.error(f"Error generating variant {variant}: {str(e)}")
                failures += 1
                results.append({
                    "success": False,
                    "error": str(e),
                    "variant": variant
                })

        return {
            "success": successes > 0,
            "subject": subject,
            "profile_name": profile_name,
            "num_variants": num_variants,
            "results": results,
            "summary": {
                "total": num_variants,
                "successes": successes,
                "failures": failures,
                "total_cost_usd": round(total_cost, 4),
                "total_time_seconds": round(total_time, 2),
                "avg_time_per_image": round(total_time / num_variants, 2) if num_variants > 0 else 0
            }
        }

    def compare_styles(
        self,
        subject: str,
        profile_names: Optional[List[str]] = None,
        variants_per_style: int = 2,
        model: Optional[str] = None,
        save_dir: str = "generated_images"
    ) -> Dict[str, Any]:
        """
        Generate same subject across multiple styles for comparison

        Args:
            subject: Subject to generate
            profile_names: List of profiles to compare (default: all)
            variants_per_style: Number of variants per style
            model: Model override
            save_dir: Directory to save images

        Returns:
            Comparison results organized by style
        """
        if profile_names is None:
            profile_names = self.style_manager.list_profiles()

        os.makedirs(save_dir, exist_ok=True)

        comparison = {
            "subject": subject,
            "styles": {},
            "summary": {
                "num_styles": len(profile_names),
                "variants_per_style": variants_per_style,
                "total_images": len(profile_names) * variants_per_style,
                "total_successes": 0,
                "total_failures": 0,
                "total_cost_usd": 0.0
            }
        }

        logger.info(f"Starting style comparison: '{subject}' across {len(profile_names)} styles")

        for profile_name in profile_names:
            logger.info(f"Generating style: {profile_name}")

            batch_result = self.generate_batch(
                subject=subject,
                profile_name=profile_name,
                num_variants=variants_per_style,
                model=model,
                save_dir=save_dir
            )

            comparison["styles"][profile_name] = batch_result

            # Update summary
            comparison["summary"]["total_successes"] += batch_result["summary"]["successes"]
            comparison["summary"]["total_failures"] += batch_result["summary"]["failures"]
            comparison["summary"]["total_cost_usd"] += batch_result["summary"]["total_cost_usd"]

        comparison["summary"]["total_cost_usd"] = round(comparison["summary"]["total_cost_usd"], 4)
        comparison["success"] = comparison["summary"]["total_successes"] > 0

        logger.info(f"Style comparison complete: {comparison['summary']['total_successes']}/{comparison['summary']['total_images']} successful")

        return comparison

    def generate_grid(
        self,
        subjects: List[str],
        profile_name: str,
        model: Optional[str] = None,
        save_dir: str = "generated_images"
    ) -> Dict[str, Any]:
        """
        Generate a grid: multiple subjects in same style (1 variant each)

        Args:
            subjects: List of subjects to generate
            profile_name: Style profile to use
            model: Model override
            save_dir: Directory to save images

        Returns:
            Grid results with all subjects
        """
        os.makedirs(save_dir, exist_ok=True)

        results = []
        successes = 0
        failures = 0
        total_cost = 0.0

        logger.info(f"Starting grid generation: {len(subjects)} subjects in '{profile_name}' style")

        for idx, subject in enumerate(subjects):
            try:
                result = self.generate_variant(
                    subject=subject,
                    profile_name=profile_name,
                    variant=0,  # First variant for each subject
                    model=model,
                    save_dir=save_dir
                )

                results.append(result)

                if result["success"]:
                    successes += 1
                    total_cost += result.get("cost_estimate_usd", 0.0)
                else:
                    failures += 1

                logger.info(f"Subject {idx+1}/{len(subjects)}: {subject} - {'✅' if result['success'] else '❌'}")

            except Exception as e:
                logger.error(f"Error generating subject '{subject}': {str(e)}")
                failures += 1
                results.append({
                    "success": False,
                    "error": str(e),
                    "subject": subject
                })

        return {
            "success": successes > 0,
            "profile_name": profile_name,
            "num_subjects": len(subjects),
            "results": results,
            "summary": {
                "total": len(subjects),
                "successes": successes,
                "failures": failures,
                "total_cost_usd": round(total_cost, 4)
            }
        }
