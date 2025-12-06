import json
import os
from datetime import datetime
from typing import Dict, Any, List


class GenerationLogger:
    """Logger for image generation requests with detailed metadata"""

    def __init__(self, log_dir: str = "logs"):
        """
        Initialize logger

        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        # JSON log file for structured data
        self.json_log_path = os.path.join(log_dir, "generations.jsonl")

        # Human-readable log file
        self.text_log_path = os.path.join(log_dir, "generations.log")

    def log_generation(self, result: Dict[str, Any]) -> None:
        """
        Log a generation request with all metadata

        Args:
            result: Dictionary with generation results from ImageGenerator
        """
        # Log to JSON Lines format (one JSON per line)
        with open(self.json_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

        # Log to human-readable format
        self._log_text(result)

    def _log_text(self, result: Dict[str, Any]) -> None:
        """Write human-readable log entry"""
        with open(self.text_log_path, "a", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"Timestamp: {result.get('timestamp', 'N/A')}\n")
            f.write(f"Status: {'SUCCESS' if result.get('success') else 'FAILED'}\n")
            f.write(f"\nModel: {result.get('model')} ({result.get('model_id')})\n")
            f.write(f"\nPrompt: {result.get('prompt')}\n")

            params = result.get("parameters", {})
            f.write(f"\nParameters:\n")
            f.write(f"  Size: {params.get('size')}\n")
            f.write(f"  Steps: {params.get('steps')}\n")
            f.write(f"  Seed: {params.get('seed')}\n")
            f.write(f"  Actual Seed: {params.get('actual_seed')}\n")

            f.write(f"\nPerformance:\n")
            f.write(f"  Latency: {result.get('latency_seconds')}s\n")
            f.write(f"  Cost Estimate: ${result.get('cost_estimate_usd', 0):.4f}\n")

            if result.get("success"):
                dims = result.get("image_dimensions", {})
                f.write(f"\nImage:\n")
                f.write(f"  Dimensions: {dims.get('width')}x{dims.get('height')}\n")
                f.write(f"  URL: {result.get('image_url')}\n")
                f.write(f"  Saved to: {result.get('saved_path')}\n")
            else:
                f.write(f"\nError: {result.get('error')}\n")

            f.write("=" * 80 + "\n\n")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics from all logged generations

        Returns:
            Dictionary with aggregated statistics
        """
        if not os.path.exists(self.json_log_path):
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
            }

        requests = self.load_all_logs()

        successful = [r for r in requests if r.get("success")]
        failed = [r for r in requests if not r.get("success")]

        total_latency = sum(r.get("latency_seconds", 0) for r in requests)
        total_cost = sum(r.get("cost_estimate_usd", 0) for r in successful)

        # Model usage
        model_counts = {}
        for r in requests:
            model = r.get("model", "unknown")
            model_counts[model] = model_counts.get(model, 0) + 1

        return {
            "total_requests": len(requests),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "total_latency_seconds": round(total_latency, 3),
            "average_latency_seconds": round(total_latency / len(requests), 3) if requests else 0,
            "total_cost_estimate_usd": round(total_cost, 4),
            "average_cost_per_image_usd": round(total_cost / len(successful), 4) if successful else 0,
            "models_used": model_counts,
        }

    def load_all_logs(self) -> List[Dict[str, Any]]:
        """Load all logged generations"""
        if not os.path.exists(self.json_log_path):
            return []

        logs = []
        with open(self.json_log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return logs

    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent log entries"""
        logs = self.load_all_logs()
        return logs[-limit:] if logs else []

    def clear_logs(self) -> None:
        """Clear all log files"""
        if os.path.exists(self.json_log_path):
            os.remove(self.json_log_path)
        if os.path.exists(self.text_log_path):
            os.remove(self.text_log_path)
