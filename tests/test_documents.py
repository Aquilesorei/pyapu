"""
Tests for strutex.documents module.
"""

import pytest
import tempfile
import os
import base64
import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strutex.documents.file_utils import (
    get_mime_type,
    read_file_as_bytes,
    encode_bytes_to_base64
)
from strutex.documents.text import _is_text_usable


class TestGetMimeType:
    """Tests for get_mime_type function."""

    def test_pdf_extension(self):
        """Test PDF file extension."""
        result = get_mime_type("document.pdf")
        assert result == "application/pdf"

    def test_png_extension(self):
        """Test PNG file extension."""
        result = get_mime_type("image.png")
        assert result == "image/png"

    def test_jpg_extension(self):
        """Test JPG file extension."""
        result = get_mime_type("photo.jpg")
        assert result == "image/jpeg"

    def test_jpeg_extension(self):
        """Test JPEG file extension."""
        result = get_mime_type("photo.jpeg")
        assert result == "image/jpeg"

    def test_xlsx_extension(self):
        """Test Excel file extension."""
        result = get_mime_type("spreadsheet.xlsx")
        assert "spreadsheet" in result or "excel" in result.lower()

    def test_txt_extension(self):
        """Test text file extension."""
        result = get_mime_type("file.txt")
        assert result == "text/plain"

    def test_unknown_extension_defaults_to_pdf(self):
        """Test unknown extension defaults to application/pdf."""
        result = get_mime_type("file.xyz123unknown")
        assert result == "application/pdf"

    def test_no_extension_defaults_to_pdf(self):
        """Test file with no extension."""
        result = get_mime_type("filename")
        assert result == "application/pdf"

    def test_path_with_directories(self):
        """Test path with directory components."""
        result = get_mime_type("/path/to/document.pdf")
        assert result == "application/pdf"


class TestReadFileAsBytes:
    """Tests for read_file_as_bytes function."""

    def test_read_existing_file(self):
        """Test reading an existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Hello, World!")
            temp_path = f.name
        
        try:
            result = read_file_as_bytes(temp_path)
            assert result == b"Hello, World!"
        finally:
            os.unlink(temp_path)

    def test_read_binary_content(self):
        """Test reading binary content."""
        binary_content = bytes([0x00, 0x01, 0x02, 0xFF, 0xFE])
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(binary_content)
            temp_path = f.name
        
        try:
            result = read_file_as_bytes(temp_path)
            assert result == binary_content
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            read_file_as_bytes("/nonexistent/path/file.txt")
        
        assert "not found" in str(exc_info.value).lower()


class TestEncodeBytesToBase64:
    """Tests for encode_bytes_to_base64 function."""

    def test_basic_encoding(self):
        """Test basic base64 encoding."""
        content = b"Hello"
        mime_type = "text/plain"
        result = encode_bytes_to_base64(content, mime_type)
        
        # Check format
        assert result.startswith("data:text/plain;base64,")
        
        # Verify encoded content
        encoded_part = result.split(",")[1]
        decoded = base64.b64decode(encoded_part)
        assert decoded == b"Hello"

    def test_pdf_mime_type(self):
        """Test encoding with PDF mime type."""
        content = b"%PDF-1.4"
        mime_type = "application/pdf"
        result = encode_bytes_to_base64(content, mime_type)
        
        assert result.startswith("data:application/pdf;base64,")

    def test_image_mime_type(self):
        """Test encoding with image mime type."""
        content = b"\x89PNG"
        mime_type = "image/png"
        result = encode_bytes_to_base64(content, mime_type)
        
        assert result.startswith("data:image/png;base64,")

    def test_empty_content(self):
        """Test encoding empty content."""
        content = b""
        result = encode_bytes_to_base64(content, "text/plain")
        
        assert result == "data:text/plain;base64,"


class TestIsTextUsable:
    """Tests for _is_text_usable helper function."""

    def test_empty_text_not_usable(self):
        """Test empty text is not usable."""
        assert _is_text_usable("") is False
        assert _is_text_usable(None) is False

    def test_short_text_not_usable(self):
        """Test text under 50 chars is not usable."""
        assert _is_text_usable("Short text") is False
        assert _is_text_usable("a" * 49) is False

    def test_whitespace_only_not_usable(self):
        """Test whitespace-only text is not usable."""
        assert _is_text_usable("   \n\n   \t\t   " * 10) is False

    def test_sparse_text_not_usable(self):
        """Test text with very few non-space chars is not usable."""
        # Lots of whitespace but only 5 actual characters
        text = "a " * 100
        # Only 100 'a' chars but might pass length check
        # Let's make sure it has at least 50 chars total but < 10 non-space
        sparse_text = " ".join(["a"] * 5) + " " * 50
        assert _is_text_usable(sparse_text) is False

    def test_valid_text_is_usable(self):
        """Test valid text is usable."""
        text = "This is a valid document with sufficient content to be considered usable for extraction."
        assert _is_text_usable(text) is True

    def test_multiline_valid_text(self):
        """Test multiline valid text is usable."""
        text = """
        Invoice Number: INV-2024-001
        Date: 2024-01-15
        Total: $1,234.56
        This document contains enough content to be processed.
        """
        assert _is_text_usable(text) is True


class TestImports:
    """Tests for module imports and exports."""

    def test_documents_package_exports(self):
        """Test documents package exports expected functions."""
        from strutex.documents import (
            pdf_to_text,
            get_mime_type,
            read_file_as_bytes,
            encode_bytes_to_base64,
            excel_to_csv_sheets
        )
        
        assert callable(pdf_to_text)
        assert callable(get_mime_type)
        assert callable(read_file_as_bytes)
        assert callable(encode_bytes_to_base64)
        assert callable(excel_to_csv_sheets)

    def test_main_package_exports(self):
        """Test main strutex package exports document functions."""
        from strutex import (
            pdf_to_text,
            get_mime_type,
            encode_bytes_to_base64,
            read_file_as_bytes,
            excel_to_csv_sheets
        )
        
        assert callable(pdf_to_text)
        assert callable(get_mime_type)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])