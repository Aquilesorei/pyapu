"""
Anthropic provider for Claude models.

Supports Claude 3.5 Sonnet, Claude 3 Opus, and other Anthropic models.
"""

import os
import json
import base64
from typing import Any, Optional

from .base import Provider
from .retry import RetryConfig, with_retry
from ..types import Schema
from ..adapters import SchemaAdapter


class AnthropicProvider(Provider, name="anthropic"):
    """
    Anthropic provider for Claude-based document extraction.
    
    Capabilities:
    - Vision (Claude 3+ models)
    - Structured JSON output
    - Large context windows (100k+ tokens)
    
    Usage:
        provider = AnthropicProvider(api_key="...", model="claude-3-5-sonnet-20241022")
        result = provider.process(file_path, prompt, schema, mime_type)
    """
    
    # Plugin v2 attributes
    strutex_plugin_version = "1.0"
    priority = 55  # Between Gemini and OpenAI
    cost = 1.5
    capabilities = ["vision", "large_context"]
    
    # Retry config
    DEFAULT_RETRY = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=60.0
    )
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: float = 120.0,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Args:
            api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
            model: Model name (claude-3-5-sonnet, claude-3-opus, etc.)
            timeout: Request timeout in seconds
            retry_config: Custom retry configuration
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.timeout = timeout
        self.retry_config = retry_config or self.DEFAULT_RETRY
        self._client = None
    
    @property
    def client(self):
        """Lazy-load the Anthropic client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("Missing API Key for Anthropic. Set ANTHROPIC_API_KEY env var.")
            try:
                from anthropic import Anthropic
                self._client = Anthropic(
                    api_key=self.api_key,
                    timeout=self.timeout
                )
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
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
        Process a document with Claude.
        
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
        
        # Build message content
        content = self._build_content(file_path, prompt, mime_type)
        
        # Use Tool Use for schema enforcement (Anthropic's structured output)
        tool = {
            "name": "extract_data",
            "description": "Extract structured data from the document according to the schema",
            "input_schema": json_schema
        }
        
        # Make request with retry
        @with_retry(config=self.retry_config)
        def call_api():
            return self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=(
                    "You are a document extraction assistant. "
                    "Use the extract_data tool to return structured data from the document."
                ),
                tools=[tool],
                tool_choice={"type": "tool", "name": "extract_data"},
                messages=[{"role": "user", "content": content}]
            )
        
        response = call_api()
        
        # Extract tool use result from response
        for block in response.content:
            if block.type == "tool_use" and block.name == "extract_data":
                return block.input
        
        # Fallback: try to parse text response as JSON
        for block in response.content:
            if block.type == "text":
                try:
                    return json.loads(block.text)
                except json.JSONDecodeError:
                    extracted = self._extract_json(block.text)
                    if extracted:
                        return extracted
        
        raise ValueError("Claude did not return structured data via tool use")
    
    def _build_content(
        self,
        file_path: str,
        prompt: str,
        mime_type: str
    ) -> list:
        """Build message content for Claude."""
        
        if self._is_image(mime_type):
            # Vision API
            with open(file_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            return [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_data
                    }
                },
                {"type": "text", "text": prompt}
            ]
        else:
            # Text-based content
            text_content = self._extract_text(file_path, mime_type)
            return [
                {
                    "type": "text",
                    "text": f"Document content:\n{text_content}\n\n{prompt}"
                }
            ]
    
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
        except Exception as e:
            import logging
            logging.getLogger("strutex.providers.anthropic").warning(
                f"Text extraction failed for {file_path} ({mime_type}): {e}"
            )
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return f"[Could not extract text from {file_path}]"
    
    def _extract_json(self, text: str) -> Optional[dict]:
        """Try to extract JSON from text."""
        import re
        
        patterns = [
            r"```json\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```",
            r"\{.*\}",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        return None
    
    @classmethod
    def health_check(cls) -> bool:
        """Check if the Anthropic provider is available."""
        try:
            from anthropic import Anthropic
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            return False
