
"""
Tests for Langdock Provider.
"""

import sys
import os
import io
import json
import pytest
import urllib.request
import urllib.error
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strutex.providers.langdock import LangdockProvider
from strutex.types import Schema, String, Object

# --- Fixtures ---

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("LANGDOCK_API_KEY", "test-key")

@pytest.fixture
def provider(mock_env):
    return LangdockProvider(api_key="test-key")

# --- Tests ---

class TestLangdockConfig:
    def test_init_defaults(self, mock_env):
        p = LangdockProvider()
        assert p.api_key == "test-key"
        assert p.model == "gemini-3-flash-preview"

    def test_init_explicit(self):
        p = LangdockProvider(api_key="custom", model="gpt-4")
        assert p.api_key == "custom"
        assert p.model == "gpt-4"

    def test_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("LANGDOCK_API_KEY", raising=False)
        p = LangdockProvider(api_key=None)
        with pytest.raises(ValueError):
            p._get_headers()

    def test_health_check(self, mock_env):
        assert LangdockProvider.health_check() is True
        
    def test_health_check_fail(self, monkeypatch):
        monkeypatch.delenv("LANGDOCK_API_KEY", raising=False)
        assert LangdockProvider.health_check() is False


class TestLangdockHelpers:
    def test_clean_json_string(self, provider):
        # Plain
        assert provider._clean_json_string('{"a":1}') == '{"a":1}'
        # Markdown
        assert provider._clean_json_string('```json\n{"a":1}\n```') == '{"a":1}'
        # Partial
        assert provider._clean_json_string('```\n{"a":1}\n```') == '{"a":1}'
        # With text
        raw = 'Here is JSON: ```json\n{"a":1}\n```'
        assert provider._clean_json_string(raw) == '{"a":1}'

    def test_build_instructions(self, provider):
        schema = Object({"field": String()})
        prompt = "Extract stuff"
        instructions = provider._build_instructions(prompt, schema)
        
        assert "You are a strict JSON" in instructions
        assert "Extract stuff" in instructions
        assert '"field":' in instructions

    def test_extract_json_from_response(self, provider):
        # Case 1: Direct output
        data = {"output": {"foo": "bar"}}
        assert provider._extract_json_from_response(data) == {"foo": "bar"}
        
        # Case 2: Message result (string)
        data = {"result": [{"role": "assistant", "content": '{"foo": "bar"}'}]}
        assert provider._extract_json_from_response(data) == {"foo": "bar"}
        
        # Case 3: Message result (blocks)
        data = {"result": [{"role": "assistant", "content": [{"type": "text", "text": '{"foo": "bar"}'}]}]}
        assert provider._extract_json_from_response(data) == {"foo": "bar"}
        
        # Case 4: Failure fallback
        data = {"other": 123}
        assert provider._extract_json_from_response(data) == data


class TestLangdockProcess:
    @patch("urllib.request.urlopen")
    def test_upload_success(self, mock_urlopen, provider, tmp_path):
        # Setup mock response
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"attachmentId": "att-123"}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        
        # Create dummy file
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"content")
        
        # Test
        att_id = provider._upload_file(str(f), "application/pdf")
        assert att_id == "att-123"
        
        # Verify request
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == LangdockProvider.UPLOAD_URL
        assert req.method == "POST"

    @patch("urllib.request.urlopen")
    def test_upload_failure(self, mock_urlopen, provider, tmp_path):
        # Setup error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="url", code=500, msg="Error", hdrs={}, fp=io.BytesIO(b"Fail")
        )
        
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"content")
        
        with pytest.raises(RuntimeError) as exc:
            provider._upload_file(str(f), "app/pdf")
        assert "Langdock upload failed (500)" in str(exc.value)

    @patch("urllib.request.urlopen")
    def test_process_success(self, mock_urlopen, provider, tmp_path):
        # Mock Upload THEN Chat
        mock_resp_upload = MagicMock()
        mock_resp_upload.read.return_value = json.dumps({"attachmentId": "att-1"}).encode()
        
        mock_resp_chat = MagicMock()
        mock_resp_chat.read.return_value = json.dumps({"output": {"data": "success"}}).encode()
        
        # Side effect: first call upload, second call chat
        # Note: both return context managers
        cm_upload = MagicMock()
        cm_upload.__enter__.return_value = mock_resp_upload
        
        cm_chat = MagicMock()
        cm_chat.__enter__.return_value = mock_resp_chat
        
        mock_urlopen.side_effect = [cm_upload, cm_chat]
        
        # Call
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"DUMMY")
        
        result = provider.process(
            str(f), "Prompt", Object({"data": String()}), "app/pdf"
        )
        
        assert result == {"data": "success"}
        
        # Verify chat request payload
        assert mock_urlopen.call_count == 2
        req = mock_urlopen.call_args[0][0] # Chat request (last call)
        assert req.full_url == LangdockProvider.CHAT_URL
        
        data = json.loads(req.data.decode())
        assert data["assistant"]["attachmentIds"] == ["att-1"]
        assert data["assistant"]["model"] == "gemini-3-flash-preview"


class TestLangdockModels:
    @patch("urllib.request.urlopen")
    def test_list_models_api(self, mock_urlopen, provider):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([
            {"id": "m1"}, {"id": "m2"}
        ]).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        
        models = provider.list_models(force_refresh=True)
        assert models == ["m1", "m2"]
        assert provider._cached_models == ["m1", "m2"]

    @patch("urllib.request.urlopen")
    def test_list_models_fallback(self, mock_urlopen, provider):
        mock_urlopen.side_effect = urllib.error.URLError("Fail")
        
        models = provider.list_models(force_refresh=True)
        # Should return keys of fallback dict
        assert "gemini-3-flash-preview" in models

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
