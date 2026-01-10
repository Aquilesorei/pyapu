"""
Integration tests for Strutex API server endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from strutex.server import create_app
import io

@pytest.fixture
def client():
    # Use a dummy provider to avoid actual LLM calls
    app = create_app(provider="mock", model="mock-model")
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@patch("strutex.processor.DocumentProcessor.aprocess")
def test_extract_generic_success(mock_aprocess, client):
    mock_aprocess.return_value = {"summary": "This is a test document."}
    
    # Create a dummy file
    file_content = b"Dummy document content"
    file_name = "test.txt"
    files = {"file": (file_name, io.BytesIO(file_content), "text/plain")}
    
    # Test with schema
    data = {
        "prompt": "Summarize this.",
        "schema": '{"type": "object", "properties": {"summary": {"type": "string"}}}'
    }
    
    response = client.post("/extract", files=files, data=data)
    
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["success"] is True
    assert json_resp["data"]["summary"] == "This is a test document."
    assert json_resp["meta"]["filename"] == file_name
    
    # Verify processor was called with correctly parsed schema
    args, kwargs = mock_aprocess.call_args
    assert kwargs["prompt"] == "Summarize this."
    assert kwargs["schema"] is not None
    assert kwargs["schema"].properties["summary"] is not None

@patch("strutex.processor.DocumentProcessor.rag_query")
def test_rag_query_success(mock_rag_query, client):
    mock_rag_query.return_value = {"answer": "Paris"}
    
    data = {
        "query": "What is the capital of France?",
        "collection": "test_collection",
        "schema": '{"type": "object", "properties": {"answer": {"type": "string"}}}'
    }
    
    response = client.post("/rag/query", data=data)
    
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["success"] is True
    assert json_resp["data"]["answer"] == "Paris"
    
    # Verify rag_query was called correctly
    mock_rag_query.assert_called_once()
    args, kwargs = mock_rag_query.call_args
    assert kwargs["query"] == "What is the capital of France?"
    assert kwargs["collection_name"] == "test_collection"
    assert kwargs["schema"] is not None
