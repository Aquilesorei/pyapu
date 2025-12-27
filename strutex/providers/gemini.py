"""
Google Gemini provider implementation.
"""

import os
from typing import Any, Optional

from .base import Provider
from ..types import Schema
from ..adapters import SchemaAdapter


# Note: GeminiProvider is registered via entry point in pyproject.toml:
# [tool.poetry.plugins."strutex.providers"]
# gemini = "strutex.providers.gemini:GeminiProvider"

class GeminiProvider(Provider):
    """
    Google Gemini provider for document extraction.
    
    Capabilities:
    - Vision (native PDF/image processing)
    - Structured JSON output
    
    Usage:
        provider = GeminiProvider(api_key="...", model="gemini-2.5-flash")
        result = provider.process(file_path, prompt, schema, mime_type)
    """
    
    # Plugin v2 attributes
    strutex_plugin_version = "1.0"
    priority = 50
    cost = 1.0
    capabilities = ["vision"]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ):
        """
        Args:
            api_key: Google API key. Falls back to GOOGLE_API_KEY env var.
            model: Gemini model name
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model
        self._client = None
    
    @property
    def client(self):
        """Lazy-load the Google GenAI client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("Missing API Key for Google Gemini.")
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client
    
    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Schema,
        mime_type: str,
        **kwargs
    ) -> Any:
        """
        Process a document with Gemini.
        
        Args:
            file_path: Path to the document
            prompt: Extraction prompt
            schema: Expected output schema
            mime_type: MIME type of the file
            
        Returns:
            Extracted data as dict
        """
        from google.genai import types as g_types
        
        # Convert schema to Google format
        google_schema = SchemaAdapter.to_google(schema)
        
        # Read file
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Configure response
        generate_config = g_types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=google_schema
        )
        
        # Call API
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    g_types.Content(
                        role="user",
                        parts=[
                            g_types.Part.from_bytes(data=file_content, mime_type=mime_type),
                            g_types.Part.from_text(text=prompt),
                        ],
                    ),
                ],
                config=generate_config,
            )
            return response.parsed
            
        except ImportError:
            raise
        except Exception as e:
            # Map common Google errors if possible, otherwise generic ProviderError
            error_str = str(e).lower()
            
            if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                from ..exceptions import RateLimitError
                raise RateLimitError(
                    f"Gemini rate limit exceeded: {e}",
                    provider="gemini",
                    details={"original_error": str(e)}
                )
            
            if "401" in error_str or "unauthenticated" in error_str or "api key" in error_str:
                from ..exceptions import AuthenticationError
                raise AuthenticationError(
                    f"Gemini authentication failed: {e}",
                    provider="gemini",
                    details={"original_error": str(e)}
                )
                
            if "404" in error_str or "not found" in error_str:
                from ..exceptions import ModelNotFoundError
                raise ModelNotFoundError(
                    model=self.model,
                    provider="gemini",
                    details={"original_error": str(e)}
                )
            
            from ..exceptions import ProviderError
            raise ProviderError(
                f"Gemini processing failed: {e}",
                provider="gemini",
                retryable="500" in error_str or "timeout" in error_str,
                details={"original_error": str(e)}
            )
    
    @classmethod
    def health_check(cls) -> bool:
        """
        Check if the Gemini provider is healthy.
        
        Returns True if the google-genai package is available.
        Does not verify API key validity (would require an API call).
        """
        try:
            from google import genai
            return True
        except ImportError:
            return False

