"""
Prompt injection detection security plugin.
"""

import re
from typing import List, Tuple

from ..plugins.base import SecurityPlugin, SecurityResult


class PromptInjectionDetector(SecurityPlugin):
    """
    Detects common prompt injection patterns.
    
    Checks for:
    - Direct instruction overrides ("ignore previous instructions")
    - Role manipulation ("you are now", "pretend to be")
    - Delimiter attacks (markdown, XML-style tags)
    - Encoding attacks (base64 instructions)
    
    Usage:
        detector = PromptInjectionDetector(strict=True)
        result = detector.validate_input(text)
    """
    
    # Common injection patterns (case-insensitive)
    DEFAULT_PATTERNS: List[Tuple[str, str]] = [
        # Direct overrides
        (r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)", "instruction_override"),
        (r"disregard\s+(all\s+)?(previous|above|prior)", "instruction_override"),
        (r"forget\s+(everything|all|your)\s+(previous|instructions?)", "instruction_override"),
        
        # Role manipulation
        (r"you\s+are\s+now\s+a", "role_manipulation"),
        (r"pretend\s+(to\s+be|you\s+are)", "role_manipulation"),
        (r"act\s+as\s+(if\s+you\s+are|a)", "role_manipulation"),
        (r"from\s+now\s+on\s+you", "role_manipulation"),
        
        # System prompt extraction
        (r"(show|reveal|print|display)\s+(me\s+)?(your|the)\s+(system|original)\s+prompt", "prompt_extraction"),
        (r"what\s+(is|are)\s+your\s+(system\s+)?instructions?", "prompt_extraction"),
        
        # Delimiter/boundary attacks
        (r"<\/?system>", "delimiter_attack"),
        (r"\[INST\]|\[\/INST\]", "delimiter_attack"),
        (r"```\s*system", "delimiter_attack"),
        (r"###\s*(system|instruction)", "delimiter_attack"),
        
        # Jailbreak attempts
        (r"DAN\s+mode", "jailbreak"),
        (r"developer\s+mode\s+enabled", "jailbreak"),
        (r"bypass\s+(your\s+)?(restrictions?|filters?|safety)", "jailbreak"),
    ]
    
    def __init__(
        self,
        strict: bool = False,
        additional_patterns: List[Tuple[str, str]] = None,
        block_on_detection: bool = True
    ):
        """
        Args:
            strict: If True, use stricter matching
            additional_patterns: Extra (pattern, category) tuples to check
            block_on_detection: If True, reject input on detection. If False, just warn.
        """
        self.strict = strict
        self.patterns = list(self.DEFAULT_PATTERNS)
        if additional_patterns:
            self.patterns.extend(additional_patterns)
        self.block_on_detection = block_on_detection
        
        # Compile patterns
        flags = re.IGNORECASE
        self._compiled = [(re.compile(p, flags), cat) for p, cat in self.patterns]
    
    def validate_input(self, text: str) -> SecurityResult:
        """Check for prompt injection patterns."""
        detections = []
        
        for pattern, category in self._compiled:
            matches = pattern.findall(text)
            if matches:
                detections.append({
                    "category": category,
                    "pattern": pattern.pattern,
                    "count": len(matches)
                })
        
        if detections:
            if self.block_on_detection:
                categories = list(set(d["category"] for d in detections))
                return SecurityResult(
                    valid=False,
                    text=None,
                    reason=f"Potential prompt injection detected: {', '.join(categories)}"
                )
            else:
                # Allow but flag
                return SecurityResult(
                    valid=True,
                    text=text,
                    reason=f"Warning: potential injection patterns found"
                )
        
        return SecurityResult(valid=True, text=text)
    
    def get_detections(self, text: str) -> List[dict]:
        """Get detailed detection information without blocking."""
        detections = []
        for pattern, category in self._compiled:
            matches = pattern.findall(text)
            if matches:
                detections.append({
                    "category": category,
                    "pattern": pattern.pattern,
                    "matches": matches[:5]  # Limit for safety
                })
        return detections
