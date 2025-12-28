"""
Langdock provider for enterprise LLM inference.

Langdock provides enterprise-grade access to multiple LLM models
with document upload and structured output support.
"""

import os
import json
import logging
from typing import Any, Optional, List

from .base import Provider
from .retry import RetryConfig, with_retry
from ..types import Schema
from ..adapters import SchemaAdapter

logger = logging.getLogger("strutex.providers.langdock")


class LangdockProvider(Provider, name="langdock"):
    """
    Langdock provider for enterprise LLM document extraction.
    
    Langdock provides:
    - Enterprise-grade API access
    - Multiple model support (GPT-4, Claude, Gemini)
    - Document upload with attachment handling
    - Structured JSON output
    
    The provider uses Langdock's inline assistant configuration
    for maximum flexibility.
    
    Usage:
        provider = LangdockProvider(model="gemini-3-flash-preview")
        result = provider.process(file_path, prompt, schema, mime_type)
        
        # With custom model
        provider = LangdockProvider(
            api_key="...",
            model="claude-3-5-sonnet"
        )
    
    Environment:
        LANGDOCK_API_KEY - Your Langdock API key
    """
    
    # Plugin v2 attributes
    strutex_plugin_version = "1.0"
    priority = 55  # Same as Anthropic
    cost = 1.0     # Enterprise pricing
    capabilities = ["vision", "enterprise", "multi_model"]
    
    # API endpoints
    UPLOAD_URL = "https://api.langdock.com/attachment/v1/upload"
    CHAT_URL = "https://api.langdock.com/assistant/v1/chat/completions"
    MODELS_URL = "https://api.langdock.com/assistant/v1/models"
    
    # Retry configuration
    DEFAULT_RETRY = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=60.0
    )
    
    # Fallback models (used when API call fails)
    FALLBACK_MODELS = {
        "gemini-3-flash-preview": "Google Gemini 2.5 Flash",
        "gemini-2.5-pro": "Google Gemini 2.5 Pro",
        "gpt-4o": "OpenAI GPT-4o",
        "gpt-4-turbo": "OpenAI GPT-4 Turbo",
        "claude-3-5-sonnet": "Anthropic Claude 3.5 Sonnet",
        "claude-3-opus": "Anthropic Claude 3 Opus",
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3-flash-preview",
        timeout: float = 120.0,
        retry_config: Optional[RetryConfig] = None,
        temperature: float = 0.0,
        assistant_name: str = "Strutex Extraction"
    ):
        """
        Args:
            api_key: Langdock API key. Falls back to LANGDOCK_API_KEY env var.
            model: Model name (gemini-3-flash-preview, gpt-4o, claude-3-5-sonnet, etc.)
            timeout: Request timeout in seconds
            retry_config: Custom retry configuration
            temperature: Model temperature (0.0 for deterministic extraction)
            assistant_name: Name for the inline assistant
        """
        self.api_key = api_key or os.getenv("LANGDOCK_API_KEY")
        self.model = model
        self.timeout = timeout
        self.retry_config = retry_config or self.DEFAULT_RETRY
        self.temperature = temperature
        self.assistant_name = assistant_name
    
    def _get_headers(self) -> dict:
        """Get authorization headers."""
        if not self.api_key:
            raise ValueError("Missing API Key for Langdock. Set LANGDOCK_API_KEY env var.")
        return {"Authorization": f"Bearer {self.api_key}"}
    
    def _upload_file(self, file_path: str, mime_type: str) -> str:
        """
        Upload a file to Langdock and return the attachment ID.
        
        Args:
            file_path: Path to the file
            mime_type: MIME type of the file
            
        Returns:
            Attachment ID
        """
        import urllib.request
        import urllib.error
        import mimetypes
        from pathlib import Path
        
        file_name = Path(file_path).name
        
        # Build multipart form data manually
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Construct the multipart body
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8") + file_content + f"\r\n--{boundary}--\r\n".encode("utf-8")
        
        headers = self._get_headers()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        
        req = urllib.request.Request(
            self.UPLOAD_URL,
            data=body,
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                attachment_id = data.get("attachmentId")
                
                if not attachment_id:
                    raise ValueError(f"No attachment ID in response: {data}")
                
                logger.debug(f"Uploaded file, attachment ID: {attachment_id}")
                return attachment_id
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"Langdock upload failed ({e.code}): {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to connect to Langdock: {e.reason}")
    
    def _build_instructions(self, prompt: str, schema: Schema) -> str:
        """Build the system instructions with schema."""
        json_schema = SchemaAdapter.to_json_schema(schema)
        schema_str = json.dumps(json_schema, indent=2)
        
        return f"""You are a strict JSON data extraction engine.

Your Task:
{prompt}

CRITICAL RULES:
1. Output Structure: You must return ONLY valid JSON.
2. Key Naming: Use the EXACT property names defined in the schema.
3. Data Types: Respect the types specified in the schema.
4. Missing Data: If a field cannot be found, set it to null.

REQUIRED OUTPUT SCHEMA:
{schema_str}

Extract the data from the attached document and return valid JSON matching this schema."""
    
    def _clean_json_string(self, content: str) -> str:
        """Strip markdown code blocks from a string."""
        content = content.strip()
        if "```json" in content:
            content = content.split("```json", 1)[1]
        elif "```" in content:
            content = content.split("```", 1)[1]
            
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
        return content.strip()
    
    def _extract_json_from_response(self, data: dict) -> Any:
        """Extract JSON result from Langdock response."""
        # Priority 1: Check if API returned parsed 'output' directly
        if "output" in data and isinstance(data["output"], (dict, list)):
            logger.debug("Received structured 'output' from API")
            return data["output"]
        
        # Priority 2: Check 'result' array for assistant's message
        if "result" in data and data["result"]:
            for msg in reversed(data["result"]):
                if msg.get("role") == "assistant":
                    content = msg.get("content")
                    
                    text_to_parse = ""
                    if isinstance(content, str):
                        text_to_parse = content
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_to_parse = block.get("text", "")
                                break
                    
                    if text_to_parse:
                        try:
                            clean_text = self._clean_json_string(text_to_parse)
                            return json.loads(clean_text)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON from response: {e}")
                            continue
        
        # Fallback: return raw data
        logger.warning("Could not extract structured JSON from response")
        return data
    
    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Schema,
        mime_type: str,
        web_search: bool = False,
        model: Optional[str] = None,
        attachment_ids: Optional[List[str]] =None,
        **kwargs
    ) -> Any:
        """
        Process a document with Langdock's inline assistant API.
        
        Uploads the file to Langdock, creates an inline assistant with
        the extraction instructions, and returns structured JSON output.
        
        Args:
            file_path: Path to the document to process.
            prompt: Extraction instruction sent as the user message.
                This tells the model what to extract from the document.
            schema: Expected output schema (Pydantic model or Schema object).
                The response will be validated against this schema.
            mime_type: MIME type of the file (e.g., "application/pdf").
            web_search: If True, enables web search capability for this request.
                Useful when extraction requires current data like exchange rates.
                Default: False.
            model: Override the default model for this request only.
                Example: "gpt-4o", "claude-3-5-sonnet", "gemini-2.5-pro".
                Default: Uses the model specified in __init__.
            attachment_ids: List of additional pre-uploaded Langdock attachment IDs
                to include with this request. These are combined with the
                automatically uploaded file. Default: None.
            **kwargs: Additional arguments (passed through but currently unused).
            
        Returns:
            dict: Extracted data matching the provided schema.
            
        Raises:
            ValueError: If API key is not configured.
            RuntimeError: If file upload or API call fails after retries.
            
        Example:
            >>> provider = LangdockProvider(model="gemini-3-flash-preview")
            >>> result = provider.process(
            ...     file_path="invoice.pdf",
            ...     prompt="Extract all invoice line items and totals",
            ...     schema=INVOICE_US,
            ...     mime_type="application/pdf",
            ...     web_search=True,  # Enable for exchange rate lookup
            ...     model="gpt-4o"    # Override model for this request
            ... )
        """
        import urllib.request
        import urllib.error
        
        # Step 1: Upload the file
        @with_retry(config=self.retry_config)
        def upload():
            return self._upload_file(file_path, mime_type)
        
        attachment_id = upload()
        
        # Step 2: Build the payload
        instructions = self._build_instructions(prompt, schema)
        json_schema = SchemaAdapter.to_json_schema(schema)
        
        # Build user message from prompt
        user_message = prompt if prompt else "Extract the data from this document."
        
        # Combine uploaded attachment with any additional attachments
        all_attachments = [attachment_id]
        if attachment_ids:
            all_attachments.extend(attachment_ids)
        
        payload = {
            "assistant": {
                "name": self.assistant_name,
                "instructions": instructions,
                "temperature": self.temperature,
                "model": model or self.model,
                "attachmentIds": all_attachments,
                "capabilities": {
                    "webSearch": web_search
                }
            },
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "output": {
                "type": "object",
                "schema": json_schema
            }
        }
        
        # Step 3: Call the chat API
        @with_retry(config=self.retry_config)
        def call_api():
            data = json.dumps(payload).encode("utf-8")
            headers = self._get_headers()
            headers["Content-Type"] = "application/json"
            
            req = urllib.request.Request(
                self.CHAT_URL,
                data=data,
                headers=headers,
                method="POST"
            )
            
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8") if e.fp else ""
                raise RuntimeError(f"Langdock API error ({e.code}): {error_body}")
            except urllib.error.URLError as e:
                raise RuntimeError(f"Failed to connect to Langdock: {e.reason}")
        
        response_data = call_api()
        
        # Step 4: Extract JSON from response
        return self._extract_json_from_response(response_data)
    
    @classmethod
    def health_check(cls) -> bool:
        """
        Check if the Langdock provider is available.
        
        Returns True if API key is set.
        """
        return bool(os.getenv("LANGDOCK_API_KEY"))
    
    def list_models(self, force_refresh: bool = False) -> List[str]:
        """
        Get list of available models from Langdock API.
        
        Args:
            force_refresh: If True, bypass cache and call API
            
        Returns:
            List of model names
        """
        # Use cached models if available
        if hasattr(self, '_cached_models') and not force_refresh:
            return self._cached_models
        
        # Try to fetch from API
        try:
            models = self._fetch_models_from_api()
            self._cached_models = models
            return models
        except Exception as e:
            logger.warning(f"Failed to fetch models from API: {e}. Using fallback list.")
            return list(self.FALLBACK_MODELS.keys())
    
    def _fetch_models_from_api(self) -> List[str]:
        """
        Fetch available models from Langdock API.
        
        Returns:
            List of model names
            
        Raises:
            RuntimeError: If API call fails
        """
        import urllib.request
        import urllib.error
        
        headers = self._get_headers()
        
        req = urllib.request.Request(
            self.MODELS_URL,
            headers=headers,
            method="GET"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30.0) as response:
                data = json.loads(response.read().decode("utf-8"))
                
                # Handle different response formats
                if isinstance(data, list):
                    # Direct list of model objects
                    models = []
                    for item in data:
                        if isinstance(item, str):
                            models.append(item)
                        elif isinstance(item, dict):
                            # Extract model ID/name from object
                            model_id = item.get("id") or item.get("name") or item.get("model")
                            if model_id:
                                models.append(model_id)
                    return models
                    
                elif isinstance(data, dict):
                    # Wrapped response with 'data' or 'models' key
                    model_list = data.get("data") or data.get("models") or data.get("items") or []
                    models = []
                    for item in model_list:
                        if isinstance(item, str):
                            models.append(item)
                        elif isinstance(item, dict):
                            model_id = item.get("id") or item.get("name") or item.get("model")
                            if model_id:
                                models.append(model_id)
                    return models
                
                logger.warning(f"Unexpected API response format: {type(data)}")
                return list(self.FALLBACK_MODELS.keys())
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"Langdock models API error ({e.code}): {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to connect to Langdock: {e.reason}")
    
    def get_model_info(self) -> dict:
        """
        Get detailed model information from API.
        
        Returns:
            Dict with model information
        """
        import urllib.request
        import urllib.error
        
        try:
            headers = self._get_headers()
            req = urllib.request.Request(
                self.MODELS_URL,
                headers=headers,
                method="GET"
            )
            
            with urllib.request.urlopen(req, timeout=30.0) as response:
                return json.loads(response.read().decode("utf-8"))
                
        except Exception as e:
            logger.warning(f"Failed to fetch model info: {e}")
            return {"models": list(self.FALLBACK_MODELS.keys())}

