"""
Ollama provider for local LLM inference.

Supports local models via Ollama for air-gapped and cost-free usage.
Respects OLLAMA_HOST environment variable for custom endpoints.
"""

import os
import json
import base64
from typing import Any, Optional, List, Dict

from .base import Provider
from .retry import RetryConfig, with_retry
from ..types import Schema
from ..adapters import SchemaAdapter


class OllamaProvider(Provider, name="ollama"):
    """
    Ollama provider for local LLM inference.
    
    Ideal for:
    - Air-gapped environments
    - Cost-free development/testing
    - Privacy-sensitive workloads
    
    Capabilities:
    - Vision (with multimodal models like llava, bakllava)
    - Structured JSON output (with grammar-based constraints)
    
    Usage:
        # Uses OLLAMA_HOST env var or defaults to localhost
        provider = OllamaProvider(model="llama3.2-vision")
        result = provider.process(file_path, prompt, schema, mime_type)
        
        # Custom host
        provider = OllamaProvider(
            host="http://192.168.1.100:11434",
            model="llama3.2-vision"
        )
    """
    
    # Plugin v2 attributes
    strutex_plugin_version = "1.0"
    priority = 40  # Lower than Gemini by default
    cost = 0.0     # Free/local
    capabilities = ["vision", "local"]
    
    # Retry config for Ollama
    DEFAULT_RETRY = RetryConfig(
        max_retries=2,
        base_delay=0.5,
        max_delay=10.0
    )
    
    def __init__(
        self,
        host: Optional[str] = None,
        model: str = "llama3.2-vision",
        timeout: float = 120.0,
        retry_config: Optional[RetryConfig] = None,
        options: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            host: Ollama API host. Falls back to OLLAMA_HOST env var,
                  then to http://localhost:11434
            model: Model name (e.g., llama3.2-vision, llava, bakllava)
            timeout: Request timeout in seconds
            retry_config: Custom retry configuration
            options: Ollama model options (temperature, num_ctx, etc.)
                     See: https://github.com/ollama/ollama/blob/main/docs/modelfile.mdx#parameter
        """
        raw_host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.host = (raw_host or "").rstrip("/")
        self.model = model
        self.timeout = timeout
        self.retry_config = retry_config or self.DEFAULT_RETRY
        self.options = options or {}
    
    def _make_request(
        self,
        endpoint: str,
        payload: dict,
        timeout: Optional[float] = None
    ) -> dict:
        """Make HTTP request to Ollama API."""
        import urllib.request
        import urllib.error
        
        url = f"{self.host}{endpoint}"
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"Ollama API error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to connect to Ollama at {self.host}: {e.reason}")
    
    def _build_prompt_with_schema(self, prompt: str, schema: Schema) -> str:
        """Build prompt with JSON schema instructions."""
        # Convert to JSON schema format
        json_schema = SchemaAdapter.to_json_schema(schema)
        
        schema_str = json.dumps(json_schema, indent=2)
        
        return f"""{prompt}

IMPORTANT: You must respond with valid JSON that matches this schema exactly:
```json
{schema_str}
```

Respond ONLY with the JSON object, no additional text or markdown."""
    
    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Schema,
        mime_type: str,
        **kwargs
    ) -> Any:
        """
        Process a document with Ollama.
        
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
        
        # Prepare the request
        messages: List[Dict[str, Any]] = [{
            "role": "user",
            "content": prompt
        }]
        
        # Handle different file types
        if self._is_visual_file(mime_type, file_path):
            # Direct image file - send as base64
            with open(file_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            messages[0]["images"] = [image_data]
        elif mime_type == "application/pdf":
            # PDF - try to convert all pages to images for vision, fall back to text
            images = self._pdf_to_images_base64(file_path)
            if images:
                messages[0]["images"] = images
            else:
                # Fall back to text extraction
                text_content = self._extract_text(file_path, mime_type)
                if text_content:
                    messages[0]["content"] = f"Document content:\n{text_content}\n\n{prompt}"
        else:
            # For non-visual files, extract text
            text_content = self._extract_text(file_path, mime_type)
            if text_content:
                messages[0]["content"] = f"Document content:\n{text_content}\n\n{prompt}"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": json_schema  # Ollama supports JSON Schema here since 0.5.0
        }
        
        # Add model options if specified
        if self.options:
            payload["options"] = self.options
        
        # Make request with retry
        @with_retry(config=self.retry_config)
        def call_api():
            return self._make_request("/api/chat", payload)
        
        response = call_api()
        
        # Parse response
        content = response.get("message", {}).get("content", "")
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # Try to extract JSON from response
            extracted = self._extract_json(content)
            if extracted:
                return extracted
            raise ValueError(f"Failed to parse JSON from Ollama response: {e}\nContent: {content[:500]}")
    
    def _is_visual_file(self, mime_type: str, file_path: str) -> bool:
        """Check if file should be processed as image."""
        # Note: PDFs are NOT directly supported by Ollama vision - they need conversion
        visual_types = {
            "image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"
        }
        return mime_type.lower() in visual_types
    
    def _pdf_to_images_base64(self, file_path: str) -> Optional[List[str]]:
        """
        Convert all PDF pages to base64 images for vision models.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of base64-encoded PNG images, or None if conversion fails
        """
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            if len(doc) == 0:
                return None
            
            images = []
            for page in doc:
                # Render at 2x resolution for better OCR
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PNG bytes
                png_bytes = pix.tobytes("png")
                images.append(base64.b64encode(png_bytes).decode("utf-8"))
            
            doc.close()
            return images if images else None
        except ImportError:
            # PyMuPDF not available, fall back to text extraction
            return None
        except Exception:
            return None
    
    def _extract_text(self, file_path: str, mime_type: str) -> Optional[str]:
        """Extract text from non-visual documents."""
        try:
            if mime_type == "application/pdf":
                from ..documents import pdf_to_text
                return pdf_to_text(file_path)
            elif mime_type in ("text/plain", "text/csv"):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            import logging
            logging.getLogger("strutex.providers.ollama").warning(
                f"Text extraction failed for {file_path} ({mime_type}): {e}"
            )
        return None
    
    def _extract_json(self, text: str) -> Optional[dict]:
        """Try to extract JSON from text that might have extra content."""
        import re
        
        # Try to find JSON in markdown code blocks
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
        """
        Check if Ollama is running and accessible.
        
        Attempts to connect to the Ollama API endpoint.
        """
        import urllib.request
        import urllib.error
        
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        try:
            req = urllib.request.Request(f"{host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models in Ollama.
        
        Returns:
            List of model names
        """
        import urllib.request
        
        try:
            url = f"{self.host}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
