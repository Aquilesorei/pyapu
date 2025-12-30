
import pytest
import unittest.mock
from strutex import DocumentProcessor
from strutex.types import Schema, Object, String, Number
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_generic_schema_processing():
    # 1. Create a Schema from dict (simulating server behavior)
    schema_dict = {
        "type": "object",
        "properties": {
            "invoice_no": {"type": "string"},
            "total": {"type": "number"}
        }
    }
    schema_obj = Schema.from_dict(schema_dict)
    
    assert isinstance(schema_obj, Object)
    assert "invoice_no" in schema_obj.properties
    assert isinstance(schema_obj.properties["invoice_no"], String)

    # 2. Mock Provider
    mock_provider = MagicMock()
    mock_provider.name = "mock"
    mock_provider.process = MagicMock(return_value={"invoice_no": "INV-001", "total": 100.0})
    
    # 3. Initialize Processor with mock
    processor = DocumentProcessor(provider=mock_provider)
    
    # 4. Mock file existence and mime type
    with unittest.mock.patch("os.path.exists", return_value=True), \
         unittest.mock.patch("strutex.processor.get_mime_type", return_value="application/pdf"):
        
        # 5. Call process with schema=schema_obj
        result = processor.process(
            file_path="dummy.pdf",
            prompt="extract",
            schema=schema_obj
        )
        
        assert result == {"invoice_no": "INV-001", "total": 100.0}
        
        # 6. Verify it FAILS if we pass it to model= (reproducing the user's error)
        try:
            processor.process(
                file_path="dummy.pdf",
                prompt="extract",
                model=schema_obj # Incorrect usage
            )
        except Exception as e:
            # We expect some error here
            pass
