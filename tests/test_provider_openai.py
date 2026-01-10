
"""
Tests for OpenAI Provider.
"""

import sys
import os
import io
import json
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strutex.providers.openai import OpenAIProvider
from strutex.types import Schema, String, Object

# --- Fixtures ---

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

@pytest.fixture
def provider(mock_env):
    return OpenAIProvider(api_key="test-key")

# --- Tests ---

class TestOpenAIConfig:
    def test_init_defaults(self, mock_env):
        p = OpenAIProvider()
        assert p.api_key == "test-key"
        assert p.model == "gpt-4o"

    def test_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        p = OpenAIProvider(api_key=None)
        with pytest.raises(ValueError):
            _ = p.client

    def test_health_check_success(self, mock_env):
        # We need to ensure import openai works or is mocked
        with patch.dict(sys.modules, {"openai": MagicMock()}):
            assert OpenAIProvider.health_check() is True

    def test_health_check_fail(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with patch.dict(sys.modules, {"openai": MagicMock()}):
            assert OpenAIProvider.health_check() is False


class TestOpenAIClient:
    def test_lazy_load(self, provider):
        assert provider._client is None
        
        mock_openai = MagicMock()
        with patch.dict(sys.modules, {"openai": mock_openai}):
            c = provider.client
            assert c is not None
            mock_openai.OpenAI.assert_called_once()
            
            # Second call
            c2 = provider.client
            assert c2 is c
            # Should not call again (mock_openai.OpenAI called once total)
            assert mock_openai.OpenAI.call_count == 1


class TestOpenAIHelpers:
    def test_is_image(self, provider):
        assert provider._is_image("image/png") is True
        assert provider._is_image("image/jpeg") is True
        assert provider._is_image("application/pdf") is False
        assert provider._is_image("text/plain") is False

    @patch("strutex.documents.pdf_to_text")
    def test_extract_text_pdf(self, mock_pdf, provider):
        mock_pdf.return_value = "PDF Content"
        text = provider._extract_text("dummy.pdf", "application/pdf")
        assert text == "PDF Content"
        mock_pdf.assert_called_with("dummy.pdf")

    def test_extract_text_plain(self, provider, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("Plain text")
        text = provider._extract_text(str(f), "text/plain")
        assert text == "Plain text"
        
    def test_extract_text_fallback(self, provider, tmp_path):
        f = tmp_path / "unknown.xyz"
        f.write_text("Fallback content")
        text = provider._extract_text(str(f), "application/unknown")
        assert text == "Fallback content"

    def test_build_messages_text(self, provider):
        provider._extract_text = MagicMock(return_value="DOC TEXT")
        
        msgs = provider._build_messages("f.txt", "Prompt", "text/plain", {"type": "object"})
        
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert "DOC TEXT" in msgs[1]["content"]
        assert "Prompt" in msgs[1]["content"]

    def test_build_messages_image(self, provider, tmp_path):
        f = tmp_path / "img.png"
        f.write_bytes(b"DATA")
        
        msgs = provider._build_messages(str(f), "Prompt", "image/png", {})
        
        content = msgs[1]["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "image_url"
        assert "base64" in content[0]["image_url"]["url"]


class TestOpenAIProcess:
    def test_process_success(self, provider):
        # Mock client
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = '{"key": "val"}'
        mock_client.chat.completions.create.return_value = mock_completion
        
        provider._client = mock_client
        provider._build_messages = MagicMock(return_value=[])
        
        result = provider.process(
            "doc.txt", "P", Object({"key": String()}), "text/plain"
        )
        
        assert result == {"key": "val"}
        
        mock_client.chat.completions.create.assert_called_once()
        kwargs = mock_client.chat.completions.create.call_args[1]
        # Verify Structured Outputs format (strict schema enforcement)
        assert kwargs["response_format"]["type"] == "json_schema"
        assert kwargs["response_format"]["json_schema"]["strict"] is True

    def test_process_json_fail(self, provider):
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = 'NOT JSON'
        mock_client.chat.completions.create.return_value = mock_completion
        
        provider._client = mock_client
        provider._build_messages = MagicMock(return_value=[])
        
        with pytest.raises(ValueError):
             provider.process(
                "doc.txt", "P", Object({"key": String()}), "text/plain"
            )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
