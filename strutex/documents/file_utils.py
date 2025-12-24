import base64
import mimetypes
import os

def get_mime_type(file_path: str) -> str:
    """Guesses the MIME type of a file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/pdf"\

def read_file_as_bytes(file_path: str) -> bytes:
    """Reads a file and returns bytes."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "rb") as f:
        return f.read()

def encode_bytes_to_base64(file_content: bytes, mime_type: str) -> str:
    """Encodes bytes to a Data URI string (e.g., 'data:image/jpeg;base64,...')."""
    base64_str = base64.b64encode(file_content).decode("utf-8")
    return f"data:{mime_type};base64,{base64_str}"