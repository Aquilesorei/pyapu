"""
Tests for FastAPI integration helpers.
"""
import pytest
from unittest.mock import MagicMock, patch
from strutex.integrations.fastapi import get_processor

# Mock FastAPI dependencies
pytest.importorskip("fastapi")

def test_get_processor_factory():
    """Verify factory returns a callable dependency."""
    dependency = get_processor(provider="test", model="fake-model", temperature=0.5)
    
    with patch("strutex.integrations.fastapi.DocumentProcessor") as MockProcessor:
        # Call the dependency
        processor = dependency()
        
        # Verify it instantiated the processor correctly
        MockProcessor.assert_called_once_with(
            provider="test",
            model_name="fake-model",
            temperature=0.5
        )
        assert processor == MockProcessor.return_value
