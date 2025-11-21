#!/usr/bin/env python3
"""
Mr. AI Evidence Validator (Platform Agnostic)
Enforces evidence-based validation for all agent responses
"""

import sys
import re
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, Dict


class EvidenceValidator:
    """Validates agent evidence blocks against Mr. AI standards"""

    # Required evidence patterns
    REQUIRED_PATTERNS = {
        "evidence_header": r"EVIDENCE\[[\w\-]+\d{4}-\d{2}-\d{2}-\d{2}:\d{2}\]:",
        "raw_output": r"RAW OUTPUT:",
        "test_results": r"├──.*:.*\[.*\]",
        "stability_check": r"[3-9]/[3-9] successful|3 (identical|successful)",
    }

    # Forbidden phrases (success theater)
    FORBIDDEN_PHRASES = [
        "should be working",
        "appears to work",
        "seems to be",
        "probably fixed",
        "might work",
        "i think it",
        "looks correct",
        "seems fine",
        "should be fine",
        "appears correct",
    ]

    def __init__(self, config_path=".mr_ai/config.yaml"):
        self.errors = []
        self.warnings = []
        self.score = 100
        self.config = self._load_config(config_path)

    def _load_config(self, config_path):
        """Load framework configuration"""
        try:
            if Path(config_path).exists():
                with open(config_path, "r") as f:
                    return yaml.safe_load(f)
        except Exception:
            pass
        return {}

    def validate_file(self, filepath: str) -> Tuple[bool, Dict]:
        """Validate an evidence file"""
        try:
            content = Path(filepath).read_text()
            return self.validate_content(content)
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return False, self.get_report()

    def validate_content(self, content: str) -> Tuple[bool, Dict]:
        """Validate evidence content"""
        self.errors = []
        self.warnings = []
        self.score = 100

        # Check for required patterns
        for pattern_name, pattern in self.REQUIRED_PATTERNS.items():
            if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                self.errors.append(f"Missing required: {pattern_name}")
                self.score -= 20

        # Check for external validation (unless config allows localhost-only)
        allow_localhost = self.config.get("validation", {}).get(
            "allow_localhost_only", False
        )

        if not allow_localhost:
            # Require external IP validation
            external_pattern = r"curl.*http[^s]?://(?!localhost|127\.0\.0\.1)"
            if not re.search(external_pattern, content, re.IGNORECASE):
                if "localhost" in content.lower() or "127.0.0.1" in content:
                    self.errors.append(
                        "Only localhost testing - no external validation"
                    )
                    self.score -= 30

        # Check for forbidden phrases
        content_lower = content.lower()
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase in content_lower:
                self.errors.append(f"Success theater detected: '{phrase}'")
                self.score -= 25

        # Check for actual command output
        if content.count("$") < 3 and content.count("#") < 3:
            self.warnings.append("Insufficient command examples")
            self.score -= 10

        # Check for output length (evidence should be substantial)
        raw_output_match = re.search(r"RAW OUTPUT:(.*)", content, re.DOTALL)
        if raw_output_match:
            raw_output = raw_output_match.group(1)
            if len(raw_output.strip()) < 100:
                self.errors.append("Raw output too short - likely summarized")
                self.score -= 30
        else:
            self.errors.append("No RAW OUTPUT section found")
            self.score -= 40

        # Determine pass/fail
        is_valid = len(self.errors) == 0 and self.score >= 70

        return is_valid, self.get_report()

    def get_report(self) -> Dict:
        """Generate validation report"""
        return {
            "valid": len(self.errors) == 0 and self.score >= 70,
            "score": max(0, self.score),
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recommendation": self.get_recommendation(),
            "config_loaded": bool(self.config),
        }

    def get_recommendation(self) -> str:
        """Get recommendation based on validation results"""
        if self.score >= 90:
            return "✅ Excellent evidence quality"
        elif self.score >= 70:
            return "⚠️ Acceptable but improve evidence"
        elif self.score >= 50:
            return "❌ Insufficient evidence - request more"
        else:
            return "🚫 Reject - likely success theater"


def main():
    """CLI for evidence validation"""
    if len(sys.argv) < 2:
        print("Usage: validate_evidence.py <evidence_file>")
        print("   or: validate_evidence.py --stdin")
        sys.exit(1)

    validator = EvidenceValidator()

    if sys.argv[1] == "--stdin":
        content = sys.stdin.read()
        is_valid, report = validator.validate_content(content)
    else:
        is_valid, report = validator.validate_file(sys.argv[1])

    # Output report
    print(json.dumps(report, indent=2))

    # Set exit code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
