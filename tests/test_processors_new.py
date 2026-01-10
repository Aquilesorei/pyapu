import pytest
from unittest.mock import Mock, MagicMock
from strutex.processors import SimpleProcessor, VerifiedProcessor, BatchProcessor
from strutex.types import Object, String
from strutex.providers.base import Provider

class MockProvider(Provider):
    name = "mock"
    def process(self, **kwargs): return {"data": "test"}
    async def aprocess(self, **kwargs): return {"data": "test"}

TEST_SCHEMA = Object(properties={"data": String()})

def test_simple_processor_calls_provider(tmp_path):
    test_file = tmp_path / "dummy.txt"
    test_file.write_text("content")
    
    mock_provider = MockProvider()
    mock_provider.process = Mock(return_value={"data": "test"})
    
    processor = SimpleProcessor(provider=mock_provider)
    result = processor.process(str(test_file), "Extract", schema=TEST_SCHEMA)
    
    assert result == {"data": "test"}
    mock_provider.process.assert_called_once()

def test_verified_processor_calls_provider_multiple_times(tmp_path):
    test_file = tmp_path / "dummy.txt"
    test_file.write_text("content")
    
    mock_provider = MockProvider()
    mock_provider.process = Mock(return_value={"data": "corrected"})
    
    # 1 initial + 2 verification passes = 3 calls
    processor = VerifiedProcessor(provider=mock_provider, verification_passes=2)
    result = processor.process(str(test_file), "Extract", schema=TEST_SCHEMA)
    
    assert result == {"data": "corrected"}
    assert mock_provider.process.call_count == 3

def test_batch_processor_concurrency(tmp_path):
    files = []
    for i in range(3):
        f = tmp_path / f"f{i}.txt"
        f.write_text("content")
        files.append(str(f))
    
    mock_provider = MockProvider()
    mock_provider.process = Mock(return_value={"data": "ok"})
    
    processor = BatchProcessor(provider=mock_provider, max_workers=2)
    batch_ctx = processor.process_batch(files, "Extract", schema=TEST_SCHEMA)
        
    assert batch_ctx.total_documents == 3
    assert len(batch_ctx.results) == 3
    assert mock_provider.process.call_count == 3
