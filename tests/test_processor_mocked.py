"""
Tests for DocumentProcessor with mocked providers.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strutex.processor import DocumentProcessor
from strutex.plugins.base import Provider, Validator, ValidationResult
from strutex.types import Object, String, Number


# Simple schema for testing
TEST_SCHEMA = Object(properties={
    "data": String(),
})


class MockProvider(Provider, name="mock_test", register=False):
    """Mock provider for testing."""
    
    def __init__(self, response=None, should_fail=False, fail_count=0):
        self.response = response or {"data": "test"}
        self.should_fail = should_fail
        self.fail_count = fail_count
        self.call_count = 0
        self.last_args = None
    
    def process(self, file_path: str, prompt: str, schema=None, mime_type: str = None, **kwargs):
        """Implement abstract process method."""
        self.call_count += 1
        
        # Read file content if exists
        content = ""
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
        
        self.last_args = {"content": content, "prompt": prompt, "schema": schema}
        
        if self.should_fail:
            if self.call_count <= self.fail_count:
                raise Exception("Mock provider failure")
        
        return self.response


class TestDocumentProcessorInit:
    """Tests for DocumentProcessor initialization."""
    
    def test_init_with_provider_instance(self):
        """Test initialization with provider instance."""
        mock = MockProvider()
        processor = DocumentProcessor(provider=mock)
        assert processor._provider == mock


class TestDocumentProcessorProcess:
    """Tests for DocumentProcessor.process method."""
    
    def test_process_returns_extracted_data(self, tmp_path):
        """Test process returns data from provider."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Invoice #12345\nTotal: $100.00")
        
        mock = MockProvider(response={"invoice_id": "12345", "total": 100.0})
        processor = DocumentProcessor(provider=mock)
        
        result = processor.process(
            file_path=str(test_file),
            prompt="Extract invoice data",
            schema=TEST_SCHEMA
        )
        
        assert result["invoice_id"] == "12345"
        assert result["total"] == 100.0
        assert mock.call_count == 1
    
    def test_process_with_pydantic_model(self, tmp_path):
        """Test process with Pydantic model."""
        from pydantic import BaseModel
        
        class Invoice(BaseModel):
            invoice_id: str
            total: float
        
        test_file = tmp_path / "invoice.txt"
        test_file.write_text("Invoice data")
        
        mock = MockProvider(response={"invoice_id": "INV-001", "total": 250.0})
        processor = DocumentProcessor(provider=mock)
        
        result = processor.process(
            file_path=str(test_file),
            prompt="Extract",
            model=Invoice
        )
        
        # Result should be validated Pydantic model
        assert isinstance(result, Invoice)
        assert result.invoice_id == "INV-001"
        assert result.total == 250.0
    
    def test_process_passes_prompt_to_provider(self, tmp_path):
        """Test prompt is passed to provider."""
        test_file = tmp_path / "doc.txt"
        test_file.write_text("content")
        
        mock = MockProvider()
        processor = DocumentProcessor(provider=mock)
        
        processor.process(str(test_file), prompt="Custom extraction prompt", schema=TEST_SCHEMA)
        
        assert "Custom extraction prompt" in mock.last_args["prompt"]
    
    def test_process_caches_result(self, tmp_path):
        """Test caching prevents redundant provider calls."""
        from strutex.cache.memory import MemoryCache
        
        test_file = tmp_path / "cached.txt"
        test_file.write_text("content to cache")
        
        mock = MockProvider(response={"cached": True})
        cache = MemoryCache()
        processor = DocumentProcessor(provider=mock, cache=cache)
        
        # First call
        result1 = processor.process(str(test_file), "Extract", schema=TEST_SCHEMA)
        assert mock.call_count == 1
        
        # Second call - should hit cache
        result2 = processor.process(str(test_file), "Extract", schema=TEST_SCHEMA)
        assert mock.call_count == 1  # No new calls
        assert result1 == result2


class TestDocumentProcessorHooks:
    """Tests for processor hooks."""
    
    def test_pre_process_hook_called(self, tmp_path):
        """Test pre-process hook is called."""
        test_file = tmp_path / "doc.txt"
        test_file.write_text("content")
        
        hook_called = []
        
        def track_hook(file_path, prompt, schema, mime_type, context):
            hook_called.append(prompt)
            return None  # No modifications
        
        mock = MockProvider()
        processor = DocumentProcessor(
            provider=mock,
            on_pre_process=track_hook
        )
        
        processor.process(str(test_file), "Original prompt", schema=TEST_SCHEMA)
        
        assert len(hook_called) == 1
        assert "Original prompt" in hook_called[0]
    
    def test_post_process_hook_modifies_result(self, tmp_path):
        """Test post-process hook can modify result."""
        test_file = tmp_path / "doc.txt"
        test_file.write_text("content")
        
        def add_metadata(result, context):
            result["_processed"] = True
            return result
        
        mock = MockProvider(response={"data": "123"})
        processor = DocumentProcessor(
            provider=mock,
            on_post_process=add_metadata
        )
        
        result = processor.process(str(test_file), "Extract", schema=TEST_SCHEMA)
        
        assert result.get("_processed") is True
        assert result["data"] == "123"
    
    def test_error_raises_without_handler(self, tmp_path):
        """Test errors propagate when provider fails."""
        test_file = tmp_path / "doc.txt"
        test_file.write_text("content")
        
        mock = MockProvider(should_fail=True, fail_count=10)
        processor = DocumentProcessor(provider=mock)
        
        with pytest.raises(Exception):
            processor.process(str(test_file), "Extract", schema=TEST_SCHEMA)


class TestDocumentProcessorFileTypes:
    """Tests for file type handling."""
    
    def test_detects_text_file(self, tmp_path):
        """Test text file is detected correctly."""
        test_file = tmp_path / "doc.txt"
        test_file.write_text("Plain text content")
        
        mock = MockProvider()
        processor = DocumentProcessor(provider=mock)
        
        processor.process(str(test_file), "Extract", schema=TEST_SCHEMA)
        
        # Provider should receive the text content
        assert "Plain text content" in mock.last_args["content"]
    
    def test_handles_missing_file(self, tmp_path):
        """Test error on missing file."""
        mock = MockProvider()
        processor = DocumentProcessor(provider=mock)
        
        with pytest.raises(FileNotFoundError):
            processor.process(str(tmp_path / "nonexistent.txt"), "Extract", schema=TEST_SCHEMA)


class TestDocumentProcessorValidation:
    """Tests for validation integration."""
    
    def test_mock_provider_called_correctly(self, tmp_path):
        """Test mock provider receives correct arguments."""
        test_file = tmp_path / "doc.txt"
        test_file.write_text("test content here")
        
        mock = MockProvider(response={"data": "extracted"})
        processor = DocumentProcessor(provider=mock)
        
        result = processor.process(str(test_file), "My prompt", schema=TEST_SCHEMA)
        
        # Verify mock was called
        assert mock.call_count == 1
        assert "My prompt" in mock.last_args["prompt"]
        assert "test content here" in mock.last_args["content"]


class TestDocumentProcessorSecurity:
    """Tests for security/sanitization integration."""
    
    def test_security_chain_can_be_passed(self, tmp_path):
        """Test security chain is accepted by processor."""
        from strutex.security import SecurityChain, InputSanitizer
        
        test_file = tmp_path / "doc.txt"
        test_file.write_text("regular content")
        
        sanitizer = InputSanitizer()
        security = SecurityChain([sanitizer])
        
        mock = MockProvider()
        processor = DocumentProcessor(
            provider=mock,
            security=security
        )
        
        # Should not raise
        result = processor.process(
            str(test_file), 
            "Extract data",
            schema=TEST_SCHEMA
        )
        
        assert mock.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
