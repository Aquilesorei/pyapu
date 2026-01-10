"""
Verification tests for advanced processors.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from strutex import DocumentProcessor
from strutex.processors import (
    FallbackProcessor, RouterProcessor, EnsembleProcessor, 
    SequentialProcessor, PrivacyProcessor, ActiveLearningProcessor,
    SimpleProcessor
)
from strutex.providers.base import Provider
from strutex.types import Object, String

class MockProvider(Provider):
    name = "mock"
    def process(self, **kwargs): return {"data": "test"}
    async def aprocess(self, **kwargs): return {"data": "test"}

TEST_SCHEMA = Object(properties={"data": String()})

def test_fallback_processor_success(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("content")
    
    # Second provider succeeds
    p1 = MockProvider()
    p1.process = Mock(side_effect=Exception("First failed"))
    p2 = MockProvider()
    p2.process = Mock(return_value={"data": "fallback_success"})
    
    fallback = FallbackProcessor(configs=[
        {"provider": p1},
        {"provider": p2}
    ])
    
    result = fallback.process(str(f), "Extract", schema=TEST_SCHEMA)
    assert result == {"data": "fallback_success"}

def test_fallback_processor_all_fail(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("content")
    
    p1 = MockProvider()
    p1.process = Mock(side_effect=Exception("Fail 1"))
    p2 = MockProvider()
    p2.process = Mock(side_effect=Exception("Fail 2"))
    
    fallback = FallbackProcessor(configs=[{"provider": p1}, {"provider": p2}])
    
    with pytest.raises(Exception, match="Fail 2"):
        fallback.process(str(f), "Extract", schema=TEST_SCHEMA)

@pytest.mark.asyncio
async def test_fallback_processor_async(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("content")
    
    p1 = MockProvider()
    async def mock_aprocess(**kwargs): return {"data": "async_success"}
    p1.aprocess = mock_aprocess
    
    fallback = FallbackProcessor(configs=[{"provider": p1}])
    result = await fallback.aprocess(str(f), "Extract", schema=TEST_SCHEMA)
    assert result == {"data": "async_success"}

def test_router_processor_routing(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Invoice 123")
    
    route_a = Mock()
    route_a.process.return_value = {"type": "A"}
    
    router = RouterProcessor(
        routes={"A": route_a},
        classifier=lambda x: "A"
    )
    
    result = router.process(str(f), "Extract")
    assert result == {"type": "A"}

def test_router_processor_default_route(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("unknown document")
    
    default_proc = Mock()
    default_proc.process.return_value = {"type": "default"}
    
    router = RouterProcessor(
        routes={"A": Mock()},
        classifier=lambda x: "B", # Non-existent route
        default_route="default",
    )
    router._routes["default"] = default_proc
    
    result = router.process(str(f), "Extract")
    assert result == {"type": "default"}

def test_ensemble_processor_consensus(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("content")
    
    p1 = Mock()
    p1.process.return_value = {"val": 1}
    p2 = Mock()
    p2.process.return_value = {"val": 1}
    judge = Mock()
    judge.process.return_value = {"val": 1, "status": "verified"}
    
    ensemble = EnsembleProcessor(providers=[p1, p2], judge=judge)
    result = ensemble.process(str(f), "Extract")
    
    assert result["status"] == "verified"

@pytest.mark.asyncio
async def test_ensemble_processor_async(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("content")
    
    p1 = Mock()
    async def mock_aprocess1(*args, **kwargs): return {"val": 1}
    p1.aprocess = mock_aprocess1
    
    p2 = Mock()
    p2.aprocess = mock_aprocess1 # Re-use the same mock coroutine
    
    judge = Mock()
    async def mock_judge_aprocess(*args, **kwargs): return {"val": 1, "synthesized": True}
    judge.aprocess = mock_judge_aprocess
    
    ensemble = EnsembleProcessor(providers=[p1, p2], judge=judge)
    result = await ensemble.aprocess(str(f), "Extract")
    assert result["synthesized"] is True

def test_privacy_processor_redaction(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Email: test@example.com")
    
    inner = Mock()
    inner.process.return_value = {"found_email": "[EMAIL_0]"}
    
    privacy = PrivacyProcessor(processor=inner)
    result = privacy.process(str(f), "Extract")
    
    assert result["found_email"] == "test@example.com"

def test_active_learning_confidence(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("content")
    
    inner = Mock()
    inner.process.return_value = {"data": "ok"}
    
    active = ActiveLearningProcessor(processor=inner, num_trials=2)
    result = active.process(str(f), "Extract")
    
    assert "_confidence" in result
    assert "_requires_review" in result

def test_sequential_processor_skeleton(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("multi-page content")
    
    inner = Mock()
    inner.process.side_effect = [{"p1": 1}, {"p2": 2}, {"p3": 3}]
    
    seq = SequentialProcessor(processor=inner)
    result = seq.process(str(f), "Extract")
    
    assert result == {"p1": 1, "p2": 2, "p3": 3}
    assert inner.process.call_count == 3
