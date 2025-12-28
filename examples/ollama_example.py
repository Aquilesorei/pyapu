"""
Local LLM extraction with Ollama.

This example shows how to use strutex with Ollama for fully local,
private document extraction - no API keys or cloud calls needed.

Requirements:
    1. Install Ollama: https://ollama.ai
    2. Pull a vision model: `ollama pull llama3.2-vision`
    3. Start Ollama: `ollama serve`
"""

import os
import sys

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strutex import DocumentProcessor
from strutex.providers import OllamaProvider
from strutex.schemas import INVOICE_GENERIC

# Get the directory of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(SCRIPT_DIR, "order.pdf")


def basic_extraction():
    """Simple extraction with Ollama."""
    
    # Create processor with Ollama provider
    processor = DocumentProcessor(
        provider=OllamaProvider(
            model="llama3.2-vision",  # Vision model for PDFs/images
            host="http://localhost:11434"  # Default Ollama host
        )
    )
    
    result = processor.process(
        file_path=PDF_PATH,
        prompt="Extract all invoice details from this document.",
        model=INVOICE_GENERIC
    )
    
    print("📄 Invoice Number:", result.invoice_number)
    print("📅 Date:", result.invoice_date)
    print("💰 Total:", result.total)
    
    return result


def with_custom_model():
    """Use a different Ollama model."""
    
    # Try different models based on your hardware
    # Smaller models: "llama3.2:3b", "phi3:mini"
    # Larger models: "llama3.1:70b", "mixtral"
    
    processor = DocumentProcessor(
        provider=OllamaProvider(
            model="llama3.2:3b",  # Smaller, faster model
            options={
                "temperature": 0.1,  # Lower = more deterministic
                "num_ctx": 4096,     # Context window
            }
        )
    )
    
    result = processor.process(
        file_path=PDF_PATH,
        prompt="Extract invoice data.",
        model=INVOICE_GENERIC
    )
    
    return result


def with_verification():
    """Add verification loop for better accuracy."""
    
    processor = DocumentProcessor(
        provider=OllamaProvider(model="llama3.2-vision")
    )
    
    # verify=True makes the LLM double-check its output
    result = processor.process(
        file_path=PDF_PATH,
        prompt="Extract all invoice details.",
        model=INVOICE_GENERIC,
        verify=True  # LLM self-checks the extraction
    )
    
    return result


def with_fallback_to_cloud():
    """Try local first, fallback to cloud if Ollama fails."""
    from strutex.providers import GeminiProvider, ProviderChain
    
    # Chain: Ollama → Gemini (cloud fallback)
    chain = ProviderChain([
        OllamaProvider(model="llama3.2-vision"),
        GeminiProvider()  # Needs GEMINI_API_KEY env var
    ])
    
    processor = DocumentProcessor(provider=chain)
    
    result = processor.process(
        file_path=PDF_PATH,
        prompt="Extract invoice data.",
        model=INVOICE_GENERIC
    )
    
    # Check which provider was used
    print(f"Used provider: {chain.last_provider.__class__.__name__}")
    
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("OLLAMA LOCAL EXTRACTION EXAMPLE")
    print("=" * 60)
    
    # Make sure Ollama is running
    print("\n⚠️  Make sure Ollama is running: `ollama serve`")
    print("⚠️  And you have a vision model: `ollama pull llama3.2-vision`\n")
    
    try:
        result = basic_extraction()
        print("\n✅ Extraction successful!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Is Ollama running? Try: `ollama serve`")
