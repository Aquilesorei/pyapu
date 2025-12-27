"""
Formatted document extractor with layout preservation, OCR, and Vision fallback.
"""

import csv
import io
import logging
import os
import re
import base64
from typing import Optional, List, Any, Literal, Union

# Core PDF extraction
try:
    import pdfplumber
    _PDFPLUMBER_AVAILABLE = True
except ImportError:
    _PDFPLUMBER_AVAILABLE = False

# OCR and Image handling
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False

from ..plugins.base import Extractor, Provider
from ..exceptions import ExtractionError

logger = logging.getLogger(__name__)

TableFormat = Literal["markdown", "csv", "plain"]


class FormattedDocExtractor(Extractor, name="formatted"):
    """
    Layout-preserving document extractor with multi-level fallback.
    
    Extraction hierarchy:
    1. Digital extraction (pdfplumber with layout mode)
    2. OCR fallback (Tesseract for scanned pages)
    3. Vision AI fallback (multimodal LLM for complex pages)
    
    """
    
    mime_types = ["application/pdf"]
    DEFAULT_PRIORITY = 60
    DEFAULT_LINE_MARGIN = 0.5
    DEFAULT_CHAR_MARGIN = 2.0
    DEFAULT_FILTER_TOLERANCE = 1.0
    
    # Heuristics
    HEADER_FOOTER_THRESHOLD = 0.10
    MIN_TEXT_DENSITY = 50
    
    priority = DEFAULT_PRIORITY
    
    def __init__(
        self,
        preserve_tables: bool = True,
        layout_mode: bool = True,
        enable_ocr: bool = True,
        ocr_language: str = "eng",
        enable_vision_fallback: bool = False,
        vision_provider: Optional[Provider] = None,
        vision_prompt: Optional[str] = None,
        line_margin: float = DEFAULT_LINE_MARGIN,
        char_margin: float = DEFAULT_CHAR_MARGIN,
        include_page_numbers: bool = True,
        table_format: TableFormat = "markdown",
        max_table_rows: Optional[int] = None,
        filter_tolerance: float = DEFAULT_FILTER_TOLERANCE,
        raise_on_error: bool = False,
        detect_headers_footers: bool = True,
        preserve_indentation: bool = True,
        min_text_density: int = 50,
    ) -> None:
        """
        Initialize the formatted extractor.
        
        Args:
            preserve_tables: Extract and format tables separately
            layout_mode: Use pdfplumber's layout preservation
            enable_ocr: Fall back to OCR for scanned/image pages
            ocr_language: Tesseract language code
            enable_vision_fallback: Use multimodal LLM as last resort
            vision_provider: Provider instance for vision extraction (e.g., GeminiProvider)
            vision_prompt: Custom prompt for vision extraction
            line_margin: Vertical margin for line grouping
            char_margin: Horizontal margin for character grouping
            include_page_numbers: Add page markers to output
            table_format: Table output format (markdown, csv, plain)
            max_table_rows: Limit rows extracted per table
            filter_tolerance: Tolerance for table region filtering
            raise_on_error: If True, raise exceptions
            detect_headers_footers: Crop headers/footers from pages
            preserve_indentation: Maintain leading whitespace structure
            min_text_density: Character threshold to trigger OCR fallback
        """
        # Input validation
        if line_margin <= 0:
            raise ValueError(f"line_margin must be positive, got {line_margin}")
        if char_margin <= 0:
            raise ValueError(f"char_margin must be positive, got {char_margin}")
        if filter_tolerance < 0:
            raise ValueError(f"filter_tolerance cannot be negative, got {filter_tolerance}")
        if max_table_rows is not None and max_table_rows <= 0:
            raise ValueError(f"max_table_rows must be positive, got {max_table_rows}")
        if table_format not in ("markdown", "csv", "plain"):
            raise ValueError(f"table_format must be markdown, csv, or plain")
        
        self.preserve_tables = preserve_tables
        self.layout_mode = layout_mode
        self.enable_ocr = enable_ocr
        self.ocr_language = ocr_language
        self.enable_vision_fallback = enable_vision_fallback
        self.vision_provider = vision_provider
        self.vision_prompt = vision_prompt or self._default_vision_prompt()
        self.line_margin = line_margin
        self.char_margin = char_margin
        self.include_page_numbers = include_page_numbers
        self.table_format = table_format
        self.max_table_rows = max_table_rows
        self.filter_tolerance = filter_tolerance
        self.raise_on_error = raise_on_error
        self.detect_headers_footers = detect_headers_footers
        self.preserve_indentation = preserve_indentation
        self.min_text_density = min_text_density
        
        # Check dependencies
        if self.enable_ocr and not _OCR_AVAILABLE:
            logger.warning("OCR requested but pytesseract/pdf2image not installed. OCR disabled.")
            self.enable_ocr = False
        
        if self.enable_vision_fallback and not self.vision_provider:
            logger.warning("Vision fallback enabled but no provider specified. Vision disabled.")
            self.enable_vision_fallback = False
    
    @staticmethod
    def _default_vision_prompt() -> str:
        """Default prompt for vision-based extraction."""
        return """Extract ALL text content from this document image.

Instructions:
- Preserve the exact layout and structure
- Format tables as Markdown tables
- Maintain paragraph breaks and spacing
- Include headers, footers, and all visible text
- For forms, preserve field labels and values
- Output plain text only, no commentary

Begin extraction:"""

    def extract(self, file_path: str) -> str:
        """
        Extract text with multi-level fallback.
        
        Hierarchy: Digital → OCR → Vision AI
        """
        if not _PDFPLUMBER_AVAILABLE:
            error_msg = "pdfplumber is required. Install with: pip install pdfplumber"
            logger.error(error_msg)
            if self.raise_on_error:
                raise ExtractionError(error_msg)
            return ""
            
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            if self.raise_on_error:
                raise FileNotFoundError(error_msg)
            return ""
        
        if not file_path.lower().endswith('.pdf'):
            logger.warning(f"File {file_path} may not be a PDF")

        pages_text: List[str] = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Processing {total_pages} pages from {file_path}")

                for i, page in enumerate(pdf.pages):
                    page_num = i + 1
                    
                    # Level 1: Try Digital Extraction
                    content = self._extract_page_digital(page)
                    extraction_method = "digital"
                    
                    # Level 2: OCR Fallback (if low text density)
                    if self.enable_ocr and len(content.strip()) < self.min_text_density:
                        logger.info(f"Page {page_num}: Low density, trying OCR...")
                        ocr_content = self._extract_page_ocr(file_path, page_num)
                        if len(ocr_content.strip()) > len(content.strip()):
                            content = ocr_content
                            extraction_method = "ocr"
                    
                    # Level 3: Vision AI Fallback (if still low density)
                    if self.enable_vision_fallback and len(content.strip()) < self.min_text_density:
                        logger.info(f"Page {page_num}: OCR insufficient, trying Vision AI...")
                        vision_content = self._extract_page_vision(file_path, page_num)
                        if vision_content:
                            content = vision_content
                            extraction_method = "vision"
                    
                    # Preserve indentation if enabled
                    if self.preserve_indentation and content:
                        content = self._preserve_indentation(content)
                    
                    # Add Page Markers
                    if self.include_page_numbers:
                        pages_text.append(f"\n--- Page {page_num} ({extraction_method}) ---\n{content}")
                    else:
                        pages_text.append(content)
                    
                    if page_num % 10 == 0:
                        logger.info(f"Processed {page_num}/{total_pages} pages")

        except Exception as e:
            error_msg = f"Extraction failed: {file_path} - {e}"
            logger.error(error_msg)
            if self.raise_on_error:
                raise ExtractionError(error_msg) from e
            return ""

        result = "\n".join(pages_text)
        
        if not self._validate_layout(result):
            logger.warning(f"Layout validation warning for {file_path}")
        
        return result

    def _extract_page_digital(self, page: Any) -> str:
        """Standard pdfplumber extraction with layout preservation."""
        parts: List[str] = []
        
        if self.detect_headers_footers:
            main_page = self._crop_header_footer(page)
        else:
            main_page = page
        
        if self.preserve_tables:
            tables = main_page.find_tables()
            table_bboxes = [t.bbox for t in tables]
            
            text = self._extract_text_excluding_regions(main_page, table_bboxes)
            if text.strip():
                parts.append(text)
            
            for i, table in enumerate(tables):
                data = table.extract()
                if data and self._validate_table_data(data):
                    fmt_table = self._format_table(data)
                    parts.append(f"\n[TABLE {i+1}]\n{fmt_table}")
        else:
            text = main_page.extract_text(
                layout=self.layout_mode,
                x_tolerance=self.char_margin,
                y_tolerance=self.line_margin,
            ) or ""
            parts.append(text)
            
        return "\n".join(parts)

    def _extract_page_ocr(self, file_path: str, page_num: int) -> str:
        """Fallback: Render page to image and run Tesseract."""
        if not _OCR_AVAILABLE:
            return ""
            
        try:
            images = convert_from_path(
                file_path, 
                first_page=page_num, 
                last_page=page_num,
                dpi=300,
            )
            if not images:
                return ""
            
            text = pytesseract.image_to_string(
                images[0], 
                lang=self.ocr_language,
                config='--psm 3'
            )
            return text
        except Exception as e:
            logger.error(f"OCR failed on page {page_num}: {e}")
            return ""

    def _extract_page_vision(self, file_path: str, page_num: int) -> str:
        """Last resort: Use multimodal LLM to extract text from page image."""
        if not self.vision_provider:
            return ""
        
        if not _OCR_AVAILABLE:
            logger.warning("Vision fallback requires pdf2image for page rendering")
            return ""
        
        try:
            # Convert page to image
            images = convert_from_path(
                file_path, 
                first_page=page_num, 
                last_page=page_num,
                dpi=150,  # Lower DPI for faster upload
            )
            if not images:
                return ""
            
            # Save to temp file for provider
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                images[0].save(tmp.name, 'PNG')
                temp_path = tmp.name
            
            try:
                # Use provider to extract text from image
                result = self.vision_provider.process(
                    file_path=temp_path,
                    prompt=self.vision_prompt,
                    schema=None,
                    mime_type="image/png",
                )
                
                # Handle different result types
                if isinstance(result, str):
                    return result
                elif isinstance(result, dict):
                    return result.get("text", str(result))
                else:
                    return str(result)
                    
            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Vision extraction failed on page {page_num}: {e}")
            return ""

    def _crop_header_footer(self, page: Any) -> Any:
        """Removes top and bottom X% of the page."""
        h = page.height
        top_crop = h * self.HEADER_FOOTER_THRESHOLD
        bottom_crop = h * (1 - self.HEADER_FOOTER_THRESHOLD)
        return page.crop((0, top_crop, page.width, bottom_crop))

    def _extract_text_excluding_regions(
        self, 
        page: Any, 
        exclude_bboxes: List[tuple]
    ) -> str:
        """Filters out characters inside table bounding boxes."""
        tolerance = self.filter_tolerance
        
        def not_in_table(obj: dict) -> bool:
            if obj.get("object_type") == "char":
                x0, top, x1, bottom = obj["x0"], obj["top"], obj["x1"], obj["bottom"]
                for (tx0, ttop, tx1, tbottom) in exclude_bboxes:
                    if (x0 + tolerance >= tx0 and x1 - tolerance <= tx1 and 
                        top + tolerance >= ttop and bottom - tolerance <= tbottom):
                        return False
            return True
        
        try:
            filtered_page = page.filter(not_in_table)
            return filtered_page.extract_text(
                layout=self.layout_mode, 
                x_tolerance=self.char_margin,
                y_tolerance=self.line_margin,
            ) or ""
        except Exception as e:
            logger.warning(f"Region filtering failed: {e}")
            return page.extract_text(layout=self.layout_mode) or ""

    def _preserve_indentation(self, text: str) -> str:
        """Preserve and normalize indentation."""
        if not text:
            return text
        
        lines = text.split('\n')
        processed_lines: List[str] = []
        
        for line in lines:
            stripped = line.lstrip(' ')
            if stripped:
                leading_spaces = len(line) - len(stripped)
                indent_level = leading_spaces // 4
                normalized_indent = "  " * indent_level
                processed_lines.append(normalized_indent + stripped)
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)

    def _validate_layout(self, text: str) -> bool:
        """Validate extracted layout quality."""
        if not text:
            return False
        
        if re.search(r'(.)\1{20,}', text):
            return False
        
        lines = text.split('\n')
        if lines:
            avg_length = sum(len(line) for line in lines) / len(lines)
            if avg_length > 500:
                return False
        
        return True

    def _validate_table_data(self, table_data: List[List[Any]]) -> bool:
        """Validate table data before formatting."""
        if not table_data or not isinstance(table_data, list):
            return False
        if len(table_data) < 1:
            return False
        return all(isinstance(row, (list, tuple)) for row in table_data)

    def _format_table(self, table_data: List[List[Any]]) -> str:
        """Format table data for LLM readability."""
        if not table_data:
            return ""
        
        if self.max_table_rows and len(table_data) > self.max_table_rows + 1:
            table_data = table_data[:self.max_table_rows + 1]
            table_data.append(["...", "(truncated)", "..."])
        
        clean_data = [
            [
                str(cell).strip().replace('\n', '<br>').replace('|', '&#124;') 
                if cell else "" 
                for cell in row
            ]
            for row in table_data
        ]
        
        if self.table_format == "markdown":
            return self._to_markdown(clean_data)
        elif self.table_format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerows(clean_data)
            return f"```csv\n{output.getvalue()}```"
        else:
            return "\n".join("\t".join(row) for row in clean_data)

    def _to_markdown(self, data: List[List[str]]) -> str:
        """Generate Markdown table."""
        if not data:
            return ""
        
        headers = data[0]
        num_cols = len(headers)
        separator = ["---"] * num_cols
        
        lines: List[str] = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(separator) + " |")
        
        for row in data[1:]:
            padded_row = (row + [""] * num_cols)[:num_cols]
            lines.append("| " + " | ".join(padded_row) + " |")
        
        return "\n".join(lines)
    
    def can_handle(self, mime_type: str) -> bool:
        """Check if this extractor can handle the given MIME type."""
        return mime_type in self.mime_types
    
    @classmethod
    def health_check(cls) -> bool:
        """Check if core dependencies are available."""
        return _PDFPLUMBER_AVAILABLE
    
    @classmethod
    def ocr_available(cls) -> bool:
        """Check if OCR dependencies are available."""
        return _OCR_AVAILABLE
