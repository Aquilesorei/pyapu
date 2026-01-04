"""
Groq provider for fast, cheap LLM inference.

Groq offers extremely fast inference with competitive pricing.
"""

import os
import json
import base64
from typing import Any, Optional

from .base import Provider
from .retry import RetryConfig, with_retry
from ..types import Schema
from ..adapters import SchemaAdapter


class GroqProvider(Provider, name="groq"):
    """
    Groq provider for ultra-fast LLM inference.
    
    Groq specializes in fast inference at lower cost than OpenAI.
    Good for high-throughput document processing.
    
    Capabilities:
    - Fast inference (100+ tokens/sec)
    - JSON mode
    - Vision (with llama-3.2-90b-vision-preview)
    
    Usage:
        provider = GroqProvider(model="llama-3.3-70b-versatile")
        result = provider.process(file_path, prompt, schema, mime_type)
    """
    
    # Plugin v2 attributes
    strutex_plugin_version = "1.0"
    priority = 45  # Between Ollama and Gemini
    cost = 0.3     # Very cheap
    capabilities = ["fast", "vision"]
    
    # Retry config
    DEFAULT_RETRY = RetryConfig(
        max_retries=3,
        base_delay=0.5,
        max_delay=30.0
    )
    
    # Available models
    MODELS = {
        "llama-3.3-70b-versatile": {"context": 128000, "vision": False},
        "llama-3.1-70b-versatile": {"context": 131072, "vision": False},
        "llama-3.2-90b-vision-preview": {"context": 8192, "vision": True},
        "llama-3.2-11b-vision-preview": {"context": 8192, "vision": True},
        "mixtral-8x7b-32768": {"context": 32768, "vision": False},
        "gemma2-9b-it": {"context": 8192, "vision": False},
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        timeout: float = 60.0,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Args:
            api_key: Groq API key. Falls back to GROQ_API_KEY env var.
            model: Model name (llama-3.3-70b-versatile, mixtral-8x7b, etc.)
            timeout: Request timeout in seconds
            retry_config: Custom retry configuration
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.timeout = timeout
        self.retry_config = retry_config or self.DEFAULT_RETRY
        self._client = None
    
    @property
    def client(self):
        """Lazy-load the Groq client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("Missing API Key for Groq. Set GROQ_API_KEY env var.")
            try:
                from groq import Groq  # type: ignore
                self._client = Groq(
                    api_key=self.api_key,
                    timeout=self.timeout
                )
            except ImportError:
                raise ImportError(
                    "groq package not installed. "
                    "Install with: pip install groq"
                )
        return self._client
    
    def _is_vision_model(self) -> bool:
        """Check if current model supports vision."""
        model_info = self.MODELS.get(self.model, {})
        return bool(model_info.get("vision", False))
    
    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Schema,
        mime_type: str,
        **kwargs
    ) -> Any:
        """
        Process a document with Groq.
        
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
        
        # Build messages based on file type and model capabilities
        if self._is_vision_model() and self._is_image(mime_type):
            messages = self._build_vision_messages(file_path, prompt, mime_type)
        else:
            messages = self._build_text_messages(file_path, prompt, mime_type)
        
        # Use Tool Use for schema enforcement
        tool = {
            "type": "function",
            "function": {
                "name": "extract_data",
                "description": "Extract structured data from the document according to the schema",
                "parameters": json_schema
            }
        }
        
        # Make request with retry
        @with_retry(config=self.retry_config)
        def call_api():
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[tool],
                tool_choice={"type": "function", "function": {"name": "extract_data"}},
                temperature=0.1,
                max_tokens=4096
            )
        
        response = call_api()
        
        # Extract tool use result
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            return json.loads(tool_calls[0].function.arguments)
        
        # Fallback: parse text
        content = response.choices[0].message.content or ""
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # Try to extract JSON
            extracted = self._extract_json(content)
            if extracted:
                return extracted
            raise ValueError(f"Failed to parse JSON from Groq response: {e}\nContent: {content[:500]}")
    
    def _build_vision_messages(
        self,
        file_path: str,
        prompt: str,
        mime_type: str
    ) -> list:
        """Build messages for vision model."""
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        return [
            {
                "role": "system",
                "content": "You are a document extraction assistant. Use the extract_data tool."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    
    def _build_text_messages(
        self,
        file_path: str,
        prompt: str,
        mime_type: str
    ) -> list:
        """Build messages for text-based processing."""
        text_content = self._extract_text(file_path, mime_type)
        
        return [
            {
                "role": "system",
                "content": "You are a document extraction assistant. Use the extract_data tool."
            },
            {
                "role": "user",
                "content": f"Document content:\n{text_content}\n\n{prompt}"
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
            logging.getLogger("strutex.providers.groq").warning(
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
        """Check if the Groq provider is available."""
        try:
            from groq import Groq  # type: ignore
            return bool(os.getenv("GROQ_API_KEY"))
        except ImportError:
            return False
