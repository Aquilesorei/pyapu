"""
Document input utilities for Strutex integrations.

Provides unified handling of file paths and in-memory file objects.
"""
import io
import os
import tempfile
from pathlib import Path
from typing import Union, Optional, BinaryIO
from contextlib import contextmanager


class DocumentInput:
    """
    A unified wrapper for document inputs that handles both file paths and BytesIO.
    
    This class provides a consistent interface for working with documents
    regardless of whether they come from disk or memory.
    
    Examples:
        # From file path
        doc = DocumentInput("/path/to/invoice.pdf")
        
        # From BytesIO
        doc = DocumentInput(io.BytesIO(pdf_bytes), filename="invoice.pdf")
        
        # Use with strutex
        with doc.as_file_path() as path:
            result = processor.process(path, schema=MySchema)
    """
    
    def __init__(
        self,
        source: Union[str, Path, BinaryIO, io.BytesIO],
        filename: Optional[str] = None,
        mime_type: Optional[str] = None
    ):
        """
        Initialize DocumentInput.
        
        Args:
            source: File path (str/Path) or file-like object (BytesIO/BinaryIO).
            filename: Original filename (required for BytesIO to infer MIME type).
            mime_type: Explicit MIME type override.
        """
        self.source = source
        self.filename = filename
        self.mime_type = mime_type
        self._temp_file: Optional[str] = None
        
        # Determine if source is a file path or file-like object
        self.is_file_path = isinstance(source, (str, Path))
        
        if self.is_file_path:
            self.path = str(source)
            if not self.filename:
                self.filename = os.path.basename(self.path)
        else:
            self.path = None
    
    @contextmanager
    def as_file_path(self):
        """
        Context manager that provides a file path for the document.
        
        For file paths, returns the path directly.
        For BytesIO, writes to a temp file and returns that path.
        
        Yields:
            str: Path to the document file.
            
        Example:
            with doc.as_file_path() as path:
                result = processor.process(path, schema=MySchema)
        """
        if self.is_file_path:
            yield self.path
        else:
            # Write BytesIO to temp file
            suffix = ""
            if self.filename:
                _, suffix = os.path.splitext(self.filename)
            
            fd, temp_path = tempfile.mkstemp(suffix=suffix)
            try:
                # Ensure we're at the start of the BytesIO
                if hasattr(self.source, 'seek'):
                    self.source.seek(0)
                
                with os.fdopen(fd, 'wb') as f:
                    f.write(self.source.read())
                
                self._temp_file = temp_path
                yield temp_path
            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                self._temp_file = None
    
    def get_bytes(self) -> bytes:
        """
        Get the document content as bytes.
        
        Returns:
            bytes: Document content.
        """
        if self.is_file_path:
            with open(self.path, 'rb') as f:
                return f.read()
        else:
            if hasattr(self.source, 'seek'):
                self.source.seek(0)
            return self.source.read()
    
    def get_mime_type(self) -> Optional[str]:
        """
        Infer MIME type from filename or return explicit override.
        
        Returns:
            str: MIME type or None if cannot be determined.
        """
        if self.mime_type:
            return self.mime_type
        
        if self.filename:
            ext = os.path.splitext(self.filename)[1].lower()
            mime_map = {
                '.pdf': 'application/pdf',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.xls': 'application/vnd.ms-excel',
                '.csv': 'text/csv',
                '.txt': 'text/plain',
                '.html': 'text/html',
            }
            return mime_map.get(ext)
        
        return None
    
    def __repr__(self) -> str:
        source_type = "path" if self.is_file_path else "bytes"
        return f"DocumentInput({source_type}, filename={self.filename!r})"
