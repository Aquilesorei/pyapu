"""
LLM Providers for strutex.

Provides the Provider base class and built-in provider implementations.

Available Providers:
- GeminiProvider: Google Gemini (vision, structured output)
- OpenAIProvider: OpenAI GPT-4o (vision, function calling)
- AnthropicProvider: Claude 3.5 (vision, large context)
- OllamaProvider: Local models via Ollama (free, air-gapped)
- GroqProvider: Ultra-fast inference (cheap, fast)
- LangdockProvider: Enterprise multi-model (Gemini, GPT, Claude)

Provider Chain:
- ProviderChain: Automatic fallback between providers
- local_first_chain(): Ollama -> Gemini -> OpenAI
- cost_optimized_chain(): Ordered by cost
"""

from .base import Provider
from .gemini import GeminiProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .ollama import OllamaProvider
from .groq import GroqProvider
from .langdock import LangdockProvider
from .hybrid import HybridProvider, HybridStrategy
from .chain import (
    ProviderChain,
    ProviderChainError,
    create_fallback_chain,
    local_first_chain,
    cost_optimized_chain,
)
from .retry import RetryConfig, with_retry, RateLimiter
from .streaming import (
    StreamChunk,
    StreamingMixin,
    StreamingProcessor,
    stream_to_string,
    stream_with_callback,
)

__all__ = [
    # Base
    "Provider",
    
    # Built-in providers
    "GeminiProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "GroqProvider",
    "LangdockProvider",
    "HybridProvider",
    "HybridStrategy",
    
    # Provider chain
    "ProviderChain",
    "ProviderChainError",
    "create_fallback_chain",
    "local_first_chain",
    "cost_optimized_chain",
    
    # Utilities
    "RetryConfig",
    "with_retry",
    "RateLimiter",
    
    # Streaming
    "StreamChunk",
    "StreamingMixin",
    "StreamingProcessor",
    "stream_to_string",
    "stream_with_callback",
]
