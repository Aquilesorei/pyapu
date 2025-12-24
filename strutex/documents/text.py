import logging
import re
import io

# Mandatory Dependencies (Standard imports)
from pypdf import PdfReader
import pdfplumber
from pdfminer.high_level import extract_text as pdfminer_extract

# Optional OCR Dependencies (Lazy loaded for Windows compatibility)
try:
    import pytesseract
    from pdf2image import convert_from_path

    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False

logger = logging.getLogger(__name__)


def _is_text_usable(text: str) -> bool:
    """
    Heuristic to check if extracted text is valid content or just garbage/whitespace.
    """
    if not text or len(text.strip()) < 50:
        return False

    # Check density: prevent "empty" extraction that is just whitespace/newlines
    non_space = len(re.sub(r'\s', '', text))
    if non_space < 10:
        return False

    return True


def _perform_ocr(file_path: str) -> str:
    """
    Fallback: Convert PDF to images and run Tesseract OCR.
    Only runs if dependencies are installed.
    """
    if not _OCR_AVAILABLE:
        logger.warning(
            f"Scanned document detected: {file_path}. "
            "OCR dependencies (pytesseract, pdf2image) are not installed. "
            "To process this file, install 'strutex[ocr]' and the Tesseract system binary."
        )
        return ""

    logger.info(f"Starting OCR extraction for {file_path}...")
    try:
        images = convert_from_path(file_path)
        text_parts = []
        for image in images:
            page_text = pytesseract.image_to_string(image)
            text_parts.append(page_text)
        return "\n".join(text_parts)

    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""


def pdf_to_text(file_path: str) -> str:
    """
    The Ultimate PDF Extractor.
    Waterfall strategy: pypdf -> pdfplumber -> pdfminer -> OCR.
    """
    text = ""

    # 1. Try pypdf (Fastest, Pure Python)
    try:
        reader = PdfReader(file_path)
        extracted_pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(extracted_pages)
        if _is_text_usable(text):
            return text
        logger.warning(f"pypdf result for {file_path} was insufficient. Falling back...")
    except Exception as e:
        logger.warning(f"pypdf failed: {e}")

    # 2. Try pdfplumber (Better Layout Handling)
    try:
        with pdfplumber.open(file_path) as pdf:
            extracted_pages = [page.extract_text() or "" for page in pdf.pages]
            text = "\n".join(extracted_pages)
            if _is_text_usable(text):
                return text
        logger.warning(f"pdfplumber result for {file_path} was insufficient. Falling back...")
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")

    # 3. Try pdfminer.six (Deep Extraction)
    try:
        text = pdfminer_extract(file_path)
        if _is_text_usable(text):
            return text
        logger.warning(f"pdfminer result for {file_path} was insufficient. Falling back to OCR...")
    except Exception as e:
        logger.warning(f"pdfminer failed: {e}")

    # 4. Try OCR (The "Nuclear Option" for Scanned Docs)
    ocr_text = _perform_ocr(file_path)
    if _is_text_usable(ocr_text):
        return ocr_text

    # Final Attempt: Return whatever partial text we found
    if text:
        return text

    raise RuntimeError(
        f"FATAL: Could not extract usable text from {file_path}. "
        "The file might be scanned/image-only, and OCR is either missing or failed."
    )