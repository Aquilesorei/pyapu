#!/usr/bin/env python3
"""
Example: Using Provider Chains for Fallback

This example demonstrates how to use ProviderChain for automatic
fallback between multiple providers, ensuring reliability.
"""

from strutex import (
    DocumentProcessor,
    ProviderChain,
    GeminiProvider,
    OllamaProvider,
    local_first_chain,
    cost_optimized_chain,
)
from strutex.providers import create_fallback_chain, ProviderChainError
from strutex.schemas import INVOICE_US


def example_basic_chain():
    """Basic provider chain with fallback."""
    print("=" * 60)
    print("Example 1: Basic Provider Chain")
    print("=" * 60)
    
    # Create a chain that tries Ollama first, then falls back to Gemini
    chain = ProviderChain([
        OllamaProvider(model="llama3.2-vision"),
        GeminiProvider()
    ])
    
    print(f"Chain: {chain}")
    print(f"Providers: {len(chain)}")
    print(f"Capabilities: {chain.capabilities}")
    
    # Use with processor (uncomment to actually run)
    # processor = DocumentProcessor(provider=chain)
    # result = processor.process("invoice.pdf", "Extract", model=INVOICE_US)
    # print(f"Used provider: {chain.last_provider.__class__.__name__}")


def example_prebuilt_chains():
    """Using pre-built convenience chains."""
    print("\n" + "=" * 60)
    print("Example 2: Pre-built Chains")
    print("=" * 60)
    
    # Local-first: Ollama -> Gemini -> OpenAI
    local_chain = local_first_chain()
    print(f"Local-first chain: {local_chain}")
    
    # Cost-optimized: Cheapest first
    cost_chain = cost_optimized_chain()
    print(f"Cost-optimized chain: {cost_chain}")
    
    # Quick creation with string names
    quick_chain = create_fallback_chain("ollama", "gemini", "openai")
    print(f"Quick fallback chain: {quick_chain}")


def example_fallback_callback():
    """Tracking fallback events."""
    print("\n" + "=" * 60)
    print("Example 3: Fallback Callbacks")
    print("=" * 60)
    
    fallback_log = []
    
    def on_fallback(provider, error):
        entry = {
            "provider": provider.__class__.__name__,
            "error": str(error)
        }
        fallback_log.append(entry)
        print(f"   {entry['provider']} failed: {error}")
    
    chain = ProviderChain(
        providers=[OllamaProvider(), GeminiProvider()],
        on_fallback=on_fallback
    )
    
    print(f"Chain created with fallback callback")
    print(f"Any fallbacks will be logged to: fallback_log")


def example_error_handling():
    """Handling when all providers fail."""
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)
    
    chain = ProviderChain(["ollama", "gemini"])
    
    print("""
    try:
        result = chain.process(file_path, prompt, schema, mime_type)
    except ProviderChainError as e:
        print(f"All providers failed: {e}")
        
        # Access individual errors
        for provider, error in e.errors:
            print(f"  - {provider.__class__.__name__}: {error}")
    """)


def example_with_processor():
    """Using chain with DocumentProcessor."""
    print("\n" + "=" * 60)
    print("Example 5: With DocumentProcessor")
    print("=" * 60)
    
    # Use local_first_chain for development
    chain = local_first_chain()
    
    print("""
    # Create processor with chain
    processor = DocumentProcessor(provider=chain)
    
    # Process document (chain handles fallback automatically)
    result = processor.process(
        file_path="invoice.pdf",
        prompt="Extract invoice details",
        model=INVOICE_US
    )
    
    # Check which provider succeeded
    print(f"Provider used: {chain.last_provider.__class__.__name__}")
    """)


if __name__ == "__main__":
    example_basic_chain()
    example_prebuilt_chains()
    example_fallback_callback()
    example_error_handling()
    example_with_processor()
    
    print("\n" + "=" * 60)
    print("Provider Chain Examples Complete!")
    print("=" * 60)
