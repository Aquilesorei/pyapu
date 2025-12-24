"""
Security chain for composing multiple security plugins.
"""

from typing import List, Dict, Any, Union

from ..plugins.base import SecurityPlugin, SecurityResult


class SecurityChain(SecurityPlugin):
    """
    Chains multiple security plugins together.
    
    Runs each plugin in sequence. If any plugin rejects, the chain stops.
    
    Usage:
        chain = SecurityChain([
            InputSanitizer(collapse_whitespace=True),
            PromptInjectionDetector(),
        ])
        result = chain.validate_input(text)
    """
    
    def __init__(self, plugins: List[SecurityPlugin]):
        """
        Args:
            plugins: List of security plugins to run in order
        """
        self.plugins = plugins
    
    def validate_input(self, text: str) -> SecurityResult:
        """Run all plugins' input validation in sequence."""
        current_text = text
        
        for plugin in self.plugins:
            result = plugin.validate_input(current_text)
            if not result.valid:
                return result
            # Use possibly-sanitized text for next plugin
            if result.text is not None:
                current_text = result.text
        
        return SecurityResult(valid=True, text=current_text)
    
    def validate_output(self, data: Dict[str, Any]) -> SecurityResult:
        """Run all plugins' output validation in sequence."""
        current_data = data
        
        for plugin in self.plugins:
            result = plugin.validate_output(current_data)
            if not result.valid:
                return result
            # Use possibly-modified data for next plugin
            if result.data is not None:
                current_data = result.data
        
        return SecurityResult(valid=True, data=current_data)
    
    def add(self, plugin: SecurityPlugin) -> "SecurityChain":
        """Add a plugin to the chain. Returns self for chaining."""
        self.plugins.append(plugin)
        return self
    
    def __len__(self) -> int:
        return len(self.plugins)
    
    def __iter__(self):
        return iter(self.plugins)


def default_security_chain() -> SecurityChain:
    """
    Create a default security chain with recommended plugins.
    
    Returns:
        SecurityChain with InputSanitizer and PromptInjectionDetector
    """
    from .sanitizer import InputSanitizer
    from .injection import PromptInjectionDetector
    from .output import OutputValidator
    
    return SecurityChain([
        InputSanitizer(
            collapse_whitespace=True,
            normalize_unicode=True,
            remove_invisible=True
        ),
        PromptInjectionDetector(block_on_detection=True),
        OutputValidator(check_secrets=True, check_prompt_leaks=True)
    ])
