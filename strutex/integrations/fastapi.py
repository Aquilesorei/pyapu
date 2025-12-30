"""
FastAPI integration for strutex.

Provides:
- Dependency factory for DocumentProcessor
- Standardized response models
- Helper for handling UploadFile
"""
from typing import Any, Dict, Optional, Type, TypeVar, Union
import shutil
import tempfile
import os
from contextlib import asynccontextmanager

try:
    from fastapi import UploadFile, HTTPException, Depends
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError(
        "FastAPI is required for this integration. "
        "Install with `pip install 'strutex[server]'`"
    )

from ..processor import DocumentProcessor
# schemas not explicitly needed for helper logic

T = TypeVar("T")

class ExtractionResponse(BaseModel):
    """Standard extraction response wrapper."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

def get_processor(
    provider: str = "gemini",
    model: str = "gemini-3-flash-preview",
    **kwargs
) -> DocumentProcessor:
    """
    Dependency factory for DocumentProcessor.
    
    Usage:
        @app.post("/extract")
        def extract(processor: DocumentProcessor = Depends(get_processor_factory("openai")))
    """
    def _dependency():
        return DocumentProcessor(provider=provider, model_name=model, **kwargs)
    return _dependency

async def save_upload_file(upload_file: UploadFile) -> str:
    """Save UploadFile to a temporary file and return the path."""
    suffix = os.path.splitext(upload_file.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(upload_file.file, tmp)
        return tmp.name

@asynccontextmanager
async def process_upload(upload_file: UploadFile):
    """
    Context manager to handle upload file lifecycle.
    Saves to temp, yields path, and auto-deletes after use.
    """
    tmp_path = await save_upload_file(upload_file)
    try:
        yield tmp_path
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
