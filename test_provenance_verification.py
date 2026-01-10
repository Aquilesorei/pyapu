"""
Verification test for ProvenanceValidator.
"""
import pytest
from unittest.mock import patch
from strutex.validators.provenance import ProvenanceValidator
from strutex.processor import DocumentProcessor
from strutex.plugins.base import Provider
from strutex.types import Object, String

# Mock similarity for unit tests
def mock_compute_similarity(text_a, text_b):
    if text_a.lower() in text_b.lower():
        return 1.0
    return 0.0

class MockProvider(Provider):
    def process(self, file_path, prompt, schema, mime_type, **kwargs):
        # Return data that contains a hallucination
        return {
            "name": "Jane Doe",
            "age": "25",
            "city": "Atlantis" # Hallucination (not in source)
        }

@patch("strutex.validators.provenance.compute_similarity", side_effect=mock_compute_similarity)
def test_provenance_validator_hallucination(mock_sim):
    source_text = "Jane Doe is 25 years old. She lives in New York."
    data = {
        "name": "Jane Doe",
        "city": "Atlantis"
    }
    
    validator = ProvenanceValidator(threshold=0.8)
    # city Atlantis should be flagged as not in New York
    result = validator.validate(data, source_text=source_text)
    
    assert not result.valid
    assert any("city" in issue for issue in result.issues)
    assert any("Atlantis" in issue for issue in result.issues)

@patch("strutex.validators.provenance.compute_similarity", side_effect=mock_compute_similarity)
def test_provenance_validator_grounded(mock_sim):
    source_text = "Jane Doe is 25 years old. She lives in New York."
    data = {
        "name": "Jane Doe",
        "age": "25"
    }
    
    validator = ProvenanceValidator(threshold=0.8)
    result = validator.validate(data, source_text=source_text)
    
    assert result.valid

@patch("strutex.validators.provenance.compute_similarity", side_effect=mock_compute_similarity)
def test_processor_integration(mock_sim):
    # Create a dummy file
    with open("test_grounding.txt", "w") as f:
        f.write("Jane Doe is 25 years old. She lives in New York.")
    
    try:
        provider = MockProvider()
        validator = ProvenanceValidator(threshold=0.8)
        processor = DocumentProcessor(provider=provider, validators=[validator])
        
        # Jane Doe 25 is fine, but Atlantis is not in the file
        result = processor.process(
            file_path="test_grounding.txt",
            prompt="Extract",
            schema=Object(properties={"name": String(), "city": String()})
        )
        
        # Validation should have logged a warning (checked via log capture usually)
        # For this test, we just ensure it ran and returned the data
        assert result["city"] == "Atlantis"
        
    finally:
        import os
        if os.path.exists("test_grounding.txt"):
            os.remove("test_grounding.txt")

if __name__ == "__main__":
    test_provenance_validator_hallucination()
    test_provenance_validator_grounded()
    test_processor_integration()
    print("All provenance tests passed!")
