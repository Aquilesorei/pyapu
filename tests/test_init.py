"""
Tests for strutex package initialization and exports.
"""

import pytest
import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class TestPackageExports:
    """Tests for main package exports."""

    def test_document_processor_export(self):
        """Test DocumentProcessor is exported."""
        from strutex import DocumentProcessor
        assert DocumentProcessor is not None

    def test_structured_prompt_export(self):
        """Test StructuredPrompt is exported."""
        from strutex import StructuredPrompt
        assert StructuredPrompt is not None

    def test_schema_types_export(self):
        """Test Schema types are exported."""
        from strutex import Schema, Type, String, Number, Integer, Boolean, Array, Object
        
        assert Schema is not None
        assert Type is not None
        assert String is not None
        assert Number is not None
        assert Integer is not None
        assert Boolean is not None
        assert Array is not None
        assert Object is not None

    def test_document_functions_export(self):
        """Test document utility functions are exported."""
        from strutex import (
            pdf_to_text,
            get_mime_type,
            encode_bytes_to_base64,
            read_file_as_bytes,
            excel_to_csv_sheets
        )
        
        assert callable(pdf_to_text)
        assert callable(get_mime_type)
        assert callable(encode_bytes_to_base64)
        assert callable(read_file_as_bytes)
        assert callable(excel_to_csv_sheets)

    def test_all_exports_list(self):
        """Test __all__ contains expected exports."""
        import strutex
        
        expected = [
            "DocumentProcessor",
            "StructuredPrompt",
            "Schema",
            "Type",
            "String",
            "Number",
            "Integer",
            "Boolean",
            "Array",
            "Object",
            "pdf_to_text",
            "get_mime_type",
            "encode_bytes_to_base64",
            "read_file_as_bytes",
            "excel_to_csv_sheets"
        ]
        
        for item in expected:
            assert item in strutex.__all__, f"{item} missing from __all__"

    def test_extract_export(self):
        """Test extract convenience function is exported."""
        from strutex import extract
        assert callable(extract)

    def test_extract_in_all(self):
        """Test extract is in __all__."""
        import strutex
        assert "extract" in strutex.__all__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])