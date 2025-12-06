"""
Style Manager for Day 18 - Brand-consistent Image Generation
Manages style profiles and prompt template assembly
"""
import json
import os
import random
from typing import Dict, Any, Optional, List


class StyleManager:
    """Manages style profiles and generates brand-consistent prompts"""

    def __init__(self, profiles_path: str = "style_profiles.json"):
        """
        Initialize StyleManager

        Args:
            profiles_path: Path to JSON file with style profiles
        """
        self.profiles_path = profiles_path
        self.profiles = self._load_profiles()

    def _load_profiles(self) -> Dict[str, Any]:
        """Load style profiles from JSON"""
        if not os.path.exists(self.profiles_path):
            raise FileNotFoundError(f"Style profiles not found: {self.profiles_path}")

        with open(self.profiles_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        Get a specific style profile

        Args:
            profile_name: Name of the profile (e.g., 'tech_startup')

        Returns:
            Style profile dictionary

        Raises:
            ValueError: If profile not found
        """
        if profile_name not in self.profiles:
            available = ", ".join(self.profiles.keys())
            raise ValueError(f"Profile '{profile_name}' not found. Available: {available}")

        return self.profiles[profile_name]

    def list_profiles(self) -> List[str]:
        """Get list of available profile names"""
        return list(self.profiles.keys())

    def build_prompt(
        self,
        subject: str,
        profile_name: str,
        additional_details: Optional[str] = None
    ) -> str:
        """
        Build a complete prompt by combining subject with style profile

        Args:
            subject: The main subject to generate (e.g., "coffee cup")
            profile_name: Style profile to use
            additional_details: Optional extra details to add

        Returns:
            Complete prompt ready for image generation
        """
        profile = self.get_profile(profile_name)

        # Build prompt: subject + optional details + style suffix
        prompt_parts = [subject]

        if additional_details:
            prompt_parts.append(additional_details)

        prompt_parts.append(profile["prompt_suffix"])

        return ", ".join(prompt_parts)

    def get_seed_for_profile(
        self,
        profile_name: str,
        variant: int = 0,
        random_seed: bool = False
    ) -> int:
        """
        Get a seed value for a specific profile and variant

        Args:
            profile_name: Style profile name
            variant: Variant number (0, 1, 2, ...) for consistent variations
            random_seed: If True, generate random seed within profile range

        Returns:
            Seed value
        """
        profile = self.get_profile(profile_name)
        seed_config = profile["seed_range"]

        if random_seed:
            return random.randint(seed_config["min"], seed_config["max"])

        # Base seed + variant offset
        return seed_config["base"] + variant

    def get_generation_config(
        self,
        subject: str,
        profile_name: str,
        variant: int = 0,
        additional_details: Optional[str] = None,
        model: Optional[str] = None,
        size: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get complete generation configuration

        Args:
            subject: Main subject
            profile_name: Style profile to use
            variant: Variant number for seed generation
            additional_details: Optional extra details
            model: Override model (default from profile or 'flux-schnell')
            size: Override aspect ratio (default from profile)

        Returns:
            Dictionary with all generation parameters
        """
        profile = self.get_profile(profile_name)

        # Build prompt
        prompt = self.build_prompt(subject, profile_name, additional_details)

        # Get seed
        seed = self.get_seed_for_profile(profile_name, variant)

        # Build config
        config = {
            "prompt": prompt,
            "seed": seed,
            "model": model or "flux-schnell",
            "size": size or profile.get("default_aspect", "square"),
            "style_profile": profile_name,
            "style_version": profile.get("version", "1.0"),
            "subject": subject,
            "variant": variant
        }

        return config

    def generate_batch_config(
        self,
        subject: str,
        profile_name: str,
        num_variants: int = 3,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate configuration for multiple variants

        Args:
            subject: Main subject
            profile_name: Style profile to use
            num_variants: Number of variants to generate
            **kwargs: Additional arguments passed to get_generation_config

        Returns:
            List of generation configurations
        """
        configs = []
        for variant in range(num_variants):
            config = self.get_generation_config(
                subject=subject,
                profile_name=profile_name,
                variant=variant,
                **kwargs
            )
            configs.append(config)

        return configs

    def compare_styles(
        self,
        subject: str,
        profile_names: Optional[List[str]] = None,
        variants_per_style: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate configurations for comparing multiple styles

        Args:
            subject: Subject to generate across all styles
            profile_names: List of profiles to compare (default: all)
            variants_per_style: Number of variants per style

        Returns:
            Dictionary mapping profile_name -> list of configs
        """
        if profile_names is None:
            profile_names = self.list_profiles()

        comparison = {}
        for profile_name in profile_names:
            comparison[profile_name] = self.generate_batch_config(
                subject=subject,
                profile_name=profile_name,
                num_variants=variants_per_style
            )

        return comparison

    def get_profile_info(self, profile_name: str) -> Dict[str, Any]:
        """
        Get human-readable profile information

        Args:
            profile_name: Style profile name

        Returns:
            Profile info without prompt_suffix (cleaner display)
        """
        profile = self.get_profile(profile_name)

        info = {
            "name": profile["name"],
            "description": profile["description"],
            "mood": profile["mood"],
            "color_palette": profile["color_palette"],
            "visual_style": profile["visual_style"],
            "aspect_ratio": profile.get("default_aspect", "square"),
            "seed_range": f"{profile['seed_range']['min']}-{profile['seed_range']['max']}",
            "version": profile.get("version", "1.0")
        }

        return info
