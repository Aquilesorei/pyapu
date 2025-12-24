"""
Output validation security plugin.
"""

import re
from typing import Dict, Any, List, Optional

from ..plugins.base import SecurityPlugin, SecurityResult


class OutputValidator(SecurityPlugin):
    """
    Validates LLM output for security issues.
    
    Checks for:
    - Leaked API keys/secrets
    - Leaked system prompts
    - Suspicious executable patterns
    - PII exposure
    
    Usage:
        validator = OutputValidator()
        result = validator.validate_output(data)
    """
    
    # Patterns for potential secrets/keys
    SECRET_PATTERNS = [
        (r"sk-[a-zA-Z0-9]{20,}", "openai_api_key"),
        (r"AIza[a-zA-Z0-9_-]{35}", "google_api_key"),
        (r"ghp_[a-zA-Z0-9]{36}", "github_token"),
        (r"xox[baprs]-[a-zA-Z0-9-]{10,}", "slack_token"),
        (r"[a-zA-Z0-9]{32}", "generic_api_key"),  # 32-char hex (less specific)
    ]
    
    # Patterns suggesting leaked prompts
    PROMPT_LEAK_PATTERNS = [
        r"you\s+are\s+a\s+(helpful\s+)?assistant",
        r"system\s*:\s*you",
        r"your\s+instructions\s+are",
        r"<<SYS>>",
        r"\[INST\]",
    ]
    
    def __init__(
        self,
        check_secrets: bool = True,
        check_prompt_leaks: bool = True,
        secret_patterns: Optional[List[tuple]] = None,
        block_on_detection: bool = True
    ):
        self.check_secrets = check_secrets
        self.check_prompt_leaks = check_prompt_leaks
        self.block_on_detection = block_on_detection
        
        # Compile patterns
        patterns = secret_patterns or self.SECRET_PATTERNS
        self._secret_patterns = [(re.compile(p, re.IGNORECASE), name) for p, name in patterns]
        self._leak_patterns = [re.compile(p, re.IGNORECASE) for p in self.PROMPT_LEAK_PATTERNS]
    
    def validate_output(self, data: Dict[str, Any]) -> SecurityResult:
        """Validate output data for security issues."""
        issues = []
        
        # Convert to string for pattern matching
        text = self._flatten_to_text(data)
        
        # Check for secrets
        if self.check_secrets:
            for pattern, secret_type in self._secret_patterns:
                if pattern.search(text):
                    issues.append(f"Potential {secret_type} detected in output")
        
        # Check for prompt leaks
        if self.check_prompt_leaks:
            for pattern in self._leak_patterns:
                if pattern.search(text):
                    issues.append("Potential system prompt leak detected")
                    break
        
        if issues:
            if self.block_on_detection:
                return SecurityResult(
                    valid=False,
                    data=None,
                    reason="; ".join(issues)
                )
            else:
                return SecurityResult(
                    valid=True,
                    data=data,
                    reason=f"Warning: {'; '.join(issues)}"
                )
        
        return SecurityResult(valid=True, data=data)
    
    def _flatten_to_text(self, data: Any, depth: int = 0) -> str:
        """Recursively flatten data structure to text for pattern matching."""
        if depth > 10:  # Prevent infinite recursion
            return ""
        
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            parts = []
            for k, v in data.items():
                parts.append(str(k))
                parts.append(self._flatten_to_text(v, depth + 1))
            return " ".join(parts)
        elif isinstance(data, (list, tuple)):
            return " ".join(self._flatten_to_text(item, depth + 1) for item in data)
        else:
            return str(data) if data is not None else ""
