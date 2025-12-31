"""
Provider chain for fallback and load balancing.

Allows chaining multiple providers with automatic fallback on failure.
"""

import logging
from typing import Any, List, Optional, Union, Callable

from .base import Provider
from ..types import Schema

logger = logging.getLogger("strutex.providers.chain")


class ProviderChain(Provider, name="chain", register=False):
    """
    Chain multiple providers with automatic fallback.
    
    Tries each provider in order until one succeeds. Useful for:
    - Reliability (fallback to backup providers)
    - Cost optimization (try cheap providers first)
    - Mixing local and cloud providers
    
    Example:
        # Fallback chain: try Ollama first, then Gemini
        chain = ProviderChain([
            OllamaProvider(model="llama3.2-vision"),
            GeminiProvider()
        ])
        
        # Use like any other provider
        result = chain.process(file_path, prompt, schema, mime_type)
        
        # Or with processor
        processor = DocumentProcessor(provider=chain)
    """
    
    # Don't auto-register this meta-provider
    strutex_plugin_version = "1.0"
    priority = 100  # High priority since it orchestrates others
    cost = 0.0  # Cost depends on which provider actually runs
    capabilities = []  # Will be computed from chain
    
    def __init__(
        self,
        providers: List[Union[Provider, str]],
        on_fallback: Optional[Callable[[Provider, Exception], None]] = None,
        stop_on_success: bool = True
    ):
        """
        Args:
            providers: List of Provider instances or provider names.
                       Tried in order until one succeeds.
            on_fallback: Optional callback when fallback occurs.
                         Called with (failed_provider, exception).
            stop_on_success: If True, stop after first success.
                            If False, all providers process (for voting).
        """
        self.providers = self._resolve_providers(providers)
        self.on_fallback = on_fallback
        self.stop_on_success = stop_on_success
        
        # Compute capabilities from all providers (safely)
        all_caps = set()
        for p in self.providers:
            all_caps.update(getattr(p, 'capabilities', []))
        self.capabilities = list(all_caps)
        
        # Track last used provider
        self._last_provider: Optional[Provider] = None
    
    def _resolve_providers(self, providers: List[Union[Provider, str]]) -> List[Provider]:
        """Convert provider names to instances."""
        from ..plugins import PluginRegistry
        
        # Map of provider names to classes (fallback for when registry isn't populated)
        PROVIDER_MAP = {
            "gemini": ".gemini:GeminiProvider",
            "openai": ".openai:OpenAIProvider",
            "anthropic": ".anthropic:AnthropicProvider",
            "ollama": ".ollama:OllamaProvider",
            "groq": ".groq:GroqProvider",
            "langdock": ".langdock:LangdockProvider",
        }
        
        resolved = []
        for p in providers:
            if isinstance(p, str):
                name = p.lower()
                
                # First try registry
                provider_cls = PluginRegistry.get("provider", name)
                
                # If not in registry, try direct import
                if provider_cls is None and name in PROVIDER_MAP:
                    module_path, class_name = PROVIDER_MAP[name].split(":")
                    try:
                        import importlib
                        # Import from strutex.providers package
                        module_name = f"strutex.providers{module_path}"
                        module = importlib.import_module(module_name)
                        provider_cls = getattr(module, class_name)
                    except (ImportError, AttributeError) as e:
                        raise ValueError(f"Failed to load provider '{name}': {e}")
                
                if provider_cls is None:
                    available = list(PROVIDER_MAP.keys())
                    raise ValueError(f"Unknown provider: {p}. Available: {available}")
                
                resolved.append(provider_cls())
            else:
                resolved.append(p)
        
        return resolved
    
    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Schema,
        mime_type: str,
        **kwargs
    ) -> Any:
        """
        Process document, trying each provider until success.
        
        Args:
            file_path: Path to document
            prompt: Extraction prompt
            schema: Output schema
            mime_type: File MIME type
            
        Returns:
            Result from first successful provider
            
        Raises:
            ProviderChainError: If all providers fail
        """
        errors = []
        
        for i, provider in enumerate(self.providers):
            provider_name = provider.__class__.__name__
            
            try:
                logger.info(f"Trying provider {i+1}/{len(self.providers)}: {provider_name}")
                
                result = provider.process(file_path, prompt, schema, mime_type, **kwargs)
                
                self._last_provider = provider
                logger.info(f"Provider {provider_name} succeeded")
                
                return result
                
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
                errors.append((provider, e))
                
                if self.on_fallback:
                    try:
                        self.on_fallback(provider, e)
                    except Exception:
                        pass  # Don't let callback errors break the chain
                
                # Continue to next provider
                continue
        
        # All providers failed
        error_summary = "; ".join(
            f"{p.__class__.__name__}: {e}" 
            for p, e in errors
        )
        raise ProviderChainError(
            f"All {len(self.providers)} providers failed: {error_summary}",
            errors=errors
        )
    
    async def aprocess(
        self,
        file_path: str,
        prompt: str,
        schema: Schema,
        mime_type: str,
        **kwargs
    ) -> Any:
        """Async version of process with fallback."""
        errors = []
        
        for i, provider in enumerate(self.providers):
            provider_name = provider.__class__.__name__
            
            try:
                logger.info(f"Trying async provider {i+1}/{len(self.providers)}: {provider_name}")
                
                result = await provider.aprocess(file_path, prompt, schema, mime_type, **kwargs)
                
                self._last_provider = provider
                logger.info(f"Provider {provider_name} succeeded")
                
                return result
                
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
                errors.append((provider, e))
                
                if self.on_fallback:
                    try:
                        self.on_fallback(provider, e)
                    except Exception:
                        pass
                
                continue
        
        error_summary = "; ".join(
            f"{p.__class__.__name__}: {e}" 
            for p, e in errors
        )
        raise ProviderChainError(
            f"All {len(self.providers)} async providers failed: {error_summary}",
            errors=errors
        )
    
    @property
    def last_provider(self) -> Optional[Provider]:
        """Return the last provider that successfully processed a request."""
        return self._last_provider
    
    def __len__(self) -> int:
        """Return number of providers in chain."""
        return len(self.providers)
    
    def __repr__(self) -> str:
        providers_str = ", ".join(p.__class__.__name__ for p in self.providers)
        return f"ProviderChain([{providers_str}])"


class ProviderChainError(Exception):
    """Raised when all providers in a chain fail."""
    
    def __init__(self, message: str, errors: List[tuple] = None):
        super().__init__(message)
        self.errors = errors or []


def create_fallback_chain(*providers: Union[Provider, str]) -> ProviderChain:
    """
    Convenience function to create a fallback chain.
    
    Example:
        chain = create_fallback_chain("ollama", "gemini", "openai")
        result = chain.process(...)
    """
    return ProviderChain(list(providers))


def local_first_chain() -> ProviderChain:
    """
    Create a chain that prefers local providers.
    
    Order: Ollama -> Gemini -> OpenAI
    
    Example:
        processor = DocumentProcessor(provider=local_first_chain())
    """
    from .ollama import OllamaProvider
    from .gemini import GeminiProvider
    from .openai import OpenAIProvider
    
    return ProviderChain([
        OllamaProvider(),
        GeminiProvider(),
        OpenAIProvider()
    ])


def cost_optimized_chain() -> ProviderChain:
    """
    Create a chain optimized for cost.
    
    Order: Ollama (free) -> Gemini -> Anthropic -> OpenAI
    """
    from .ollama import OllamaProvider
    from .gemini import GeminiProvider
    from .anthropic import AnthropicProvider
    from .openai import OpenAIProvider
    
    return ProviderChain([
        OllamaProvider(),      # Free
        GeminiProvider(),      # Cost: 1.0
        AnthropicProvider(),   # Cost: 1.5
        OpenAIProvider()       # Cost: 2.0
    ])
