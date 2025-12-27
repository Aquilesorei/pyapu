"""
OpenAI provider for GPT models.

Supports GPT-4o, GPT-4 Vision, and other OpenAI models.
"""

import os
import json
import base64
from typing import Any, Optional

from .base import Provider
from .retry import RetryConfig, with_retry
from ..types import Schema
from ..adapters import SchemaAdapter


class OpenAIProvider(Provider, name="openai"):
    """
    OpenAI provider for GPT-based document extraction.
    
    Capabilities:
    - Vision (GPT-4o, GPT-4 Vision)
    - Structured JSON output (with response_format)
    - Function calling for schema enforcement
    
    Usage:
        provider = OpenAIProvider(api_key="...", model="gpt-4o")
        result = provider.process(file_path, prompt, schema, mime_type)
    """
    
    # Plugin v2 attributes
    strutex_plugin_version = "1.0"
    priority = 60  # Higher than Ollama
    cost = 2.0     # More expensive
    capabilities = ["vision", "function_calling"]
    
    # Retry config for OpenAI
    DEFAULT_RETRY = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=60.0,
        retry_on=(Exception,)  # Will be refined to specific errors
    )
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,
        timeout: float = 120.0,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Args:
            api_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.
            model: Model name (gpt-4o, gpt-4-vision-preview, gpt-4-turbo, etc.)
            base_url: Custom API base URL (for Azure, proxies, etc.)
            timeout: Request timeout in seconds
            retry_config: Custom retry configuration
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.retry_config = retry_config or self.DEFAULT_RETRY
        self._client = None
    
    @property
    def client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("Missing API Key for OpenAI. Set OPENAI_API_KEY env var.")
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
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
        Process a document with OpenAI.
        
        Args:
            file_path: Path to the document
            prompt: Extraction prompt
            schema: Expected output schema
            mime_type: MIME type of the file
            
        Returns:
            Extracted data as dict
        """
        # Convert schema to JSON schema
        json_schema = SchemaAdapter.to_json_schema(schema)
        
        # Build messages
        messages = self._build_messages(file_path, prompt, mime_type, json_schema)
        
        # Make request with retry
        @with_retry(config=self.retry_config)
        def call_api():
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.1,  # Low temp for more consistent extraction
                    max_tokens=4096
                )
            except Exception as e:
                # Map OpenAI errors
                error_str = str(e).lower()
                
                if "rate limit" in error_str or "429" in error_str:
                    from ..exceptions import RateLimitError
                    raise RateLimitError(
                        f"OpenAI rate limit exceeded: {e}",
                        provider="openai",
                        details={"original_error": str(e)}
                    )
                
                if "authentication" in error_str or "api key" in error_str or "401" in error_str:
                    from ..exceptions import AuthenticationError
                    raise AuthenticationError(
                        f"OpenAI authentication failed: {e}",
                        provider="openai",
                        details={"original_error": str(e)}
                    )
                    
                if "not found" in error_str or "404" in error_str:
                    from ..exceptions import ModelNotFoundError
                    raise ModelNotFoundError(
                        model=self.model,
                        provider="openai",
                        details={"original_error": str(e)}
                    )

                from ..exceptions import ProviderError
                raise ProviderError(
                    f"OpenAI request failed: {e}",
                    provider="openai",
                    retryable="timeout" in error_str or "500" in error_str,
                    details={"original_error": str(e)}
                ) from e
        
        response = call_api()
        
        # Parse response
        content = response.choices[0].message.content
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from OpenAI response: {e}\nContent: {content[:500]}")
    
    def _build_messages(
        self,
        file_path: str,
        prompt: str,
        mime_type: str,
        json_schema: dict
    ) -> list:
        """Build messages for the OpenAI API."""
        
        schema_str = json.dumps(json_schema, indent=2)
        
        system_message = {
            "role": "system",
            "content": (
                "You are a document extraction assistant. "
                "Extract structured data from documents and return valid JSON only. "
                "Follow the provided schema exactly."
            )
        }
        
        # Build user message with file content
        if self._is_image(mime_type):
            # Vision API - send as image
            with open(file_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            user_content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}",
                        "detail": "high"
                    }
                },
                {
                    "type": "text",
                    "text": f"{prompt}\n\nRespond with JSON matching this schema:\n```json\n{schema_str}\n```"
                }
            ]
        elif mime_type == "application/pdf":
            # GPT-4o can handle PDFs as images (each page)
            # For simplicity, extract text first
            text_content = self._extract_text(file_path, mime_type)
            user_content = (
                f"Document content:\n{text_content}\n\n"
                f"{prompt}\n\n"
                f"Respond with JSON matching this schema:\n```json\n{schema_str}\n```"
            )
        else:
            # Text-based file
            text_content = self._extract_text(file_path, mime_type)
            user_content = (
                f"Document content:\n{text_content}\n\n"
                f"{prompt}\n\n"
                f"Respond with JSON matching this schema:\n```json\n{schema_str}\n```"
            )
        
        user_message = {
            "role": "user",
            "content": user_content
        }
        
        return [system_message, user_message]
    
    def _is_image(self, mime_type: str) -> bool:
        """Check if MIME type is an image."""
        return mime_type.lower() in {
            "image/png", "image/jpeg", "image/jpg",
            "image/webp", "image/gif"
        }
    
    def _extract_text(self, file_path: str, mime_type: str) -> str:
        """Extract text from a document."""
        try:
            if mime_type == "application/pdf":
                from ..documents import pdf_to_text
                return pdf_to_text(file_path)
            elif mime_type in ("text/plain", "text/csv"):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            elif "spreadsheet" in mime_type or "excel" in mime_type:
                from ..documents import excel_to_csv_sheets
                sheets = excel_to_csv_sheets(file_path)
                return "\n\n".join(f"Sheet: {name}\n{content}" 
                                  for name, content in sheets.items())
        except ImportError:
            # Missing dependency for PDF/Excel extraction
            return f"[Missing dependency for {mime_type} extraction]"
        except Exception as e:
             # Log warning but fallback to plain text read
             pass
        
        # Fallback: try to read as text
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            from ..exceptions import DocumentParseError
            raise DocumentParseError(
                f"Could not extract text from {file_path}",
                file_path=file_path,
                mime_type=mime_type
            )
    
    @classmethod
    def health_check(cls) -> bool:
        """
        Check if the OpenAI provider is available.
        
        Returns True if the openai package is installed and API key is set.
        """
        try:
            from openai import OpenAI
            return bool(os.getenv("OPENAI_API_KEY"))
        except ImportError:
            return False
