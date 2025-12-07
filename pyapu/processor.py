import os
import mimetypes
from typing import Any, Optional

from .documents import get_mime_type
from .types import Schema
from .adapters import SchemaAdapter


class DocumentProcessor:
    def __init__(
            self,
            provider: str = "google",
            model_name: str = "gemini-2.5-flash",
            api_key: Optional[str] = None
    ):
        self.provider = provider.lower()
        self.model_name = model_name
        self.api_key = api_key
        self.client = self._initialize_client()

    def _initialize_client(self):
        if self.provider == "google":
            from google import genai
            key = self.api_key or os.getenv("GOOGLE_API_KEY")
            if not key:
                raise ValueError("Missing API Key for Google.")
            return genai.Client(api_key=key)

        elif self.provider == "openai":
            from openai import OpenAI
            key = self.api_key or os.getenv("OPENAI_API_KEY")
            return OpenAI(api_key=key)

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def process(self, file_path: str, prompt: str, schema: Schema) -> Any:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Automatic MIME Type detection
        mime_type, _ = get_mime_type(file_path)

        if self.provider == "google":
            return self._process_google(file_path, prompt, schema, mime_type)
        elif self.provider == "openai":
            return self._process_openai(file_path, prompt, schema, mime_type)
        return None

    def _process_google(self, file_path: str, prompt: str, schema: Schema, mime_type: str):
        from google.genai import types as g_types

        # 1. Schema translation
        google_schema = SchemaAdapter.to_google(schema)

        # 2. Read binary file
        with open(file_path, "rb") as f:
            file_content = f.read()

        # 3. Configuration & Call
        generate_config = g_types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=google_schema
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                g_types.Content(
                    role="user",
                    parts=[
                        # Use dynamically detected mime_type
                        g_types.Part.from_bytes(data=file_content, mime_type=mime_type),
                        g_types.Part.from_text(text=prompt),
                    ],
                ),
            ],
            config=generate_config,
        )

        return response.parsed

    def _process_openai(self, file_path: str, prompt: str, schema: Schema, mime_type: str):
        # Placeholder for now.
        # Note: OpenAI does not handle native PDFs via standard ChatCompletion endpoint (except gpt-4o with images).
        # Text must be extracted or PDF pages converted to images for GPT-4o.
        raise NotImplementedError("OpenAI implementation coming in the next step!")