# Extractors

Extract text from documents for LLM processing.

---

## Overview

Extractors convert document files (PDF, images, spreadsheets) into text that can be sent to an LLM.

```python
from strutex import PDFExtractor, get_extractor

# Direct usage
extractor = PDFExtractor()
text = extractor.extract("invoice.pdf")

# Auto-select by MIME type
extractor = get_extractor("application/pdf")
text = extractor.extract("invoice.pdf")
```

---

## Built-in Extractors

### PDFExtractor

Uses a waterfall strategy: pypdf → pdfplumber → pdfminer → OCR.

```python
from strutex import PDFExtractor

extractor = PDFExtractor()
text = extractor.extract("document.pdf")
```

### ImageExtractor

Uses Tesseract OCR. Requires `pytesseract` and `PIL`.

```python
from strutex import ImageExtractor

extractor = ImageExtractor()
text = extractor.extract("scan.png")
```

!!! note "OCR Dependencies"
Install with: `pip install strutex[ocr]`

### ExcelExtractor

Converts spreadsheets to CSV text representation.

```python
from strutex import ExcelExtractor

extractor = ExcelExtractor()
text = extractor.extract("data.xlsx")
```

### GlinerExtractor

Fast, local entity extraction using [GLiNER](https://github.com/urchade/GLiNER) - a zero-shot NER model.

!!! tip "When to Use" - **Speed**: 10-100x faster than LLM calls - **Cost**: Runs locally, no API costs - **Hybrid**: Pre-extract entities, refine with LLM

```python
from strutex.extractors import GlinerExtractor

# Default labels (person, company, date, money, etc.)
extractor = GlinerExtractor()
result = extractor.extract("invoice.pdf")

# Custom labels for your domain
extractor = GlinerExtractor(
    labels=["container_number", "vessel", "port", "weight"],
    threshold=0.3  # Confidence threshold
)
result = extractor.extract("bill_of_lading.pdf")

# Get structured output (not formatted string)
entities = extractor.extract_structured("invoice.pdf")
# Returns: {"date": [{"text": "2024-01-15", "score": 0.92}], ...}
```

**Hybrid Pipeline** - Use GLiNER for speed, LLM for accuracy:

```python
from strutex import DocumentProcessor
from strutex.extractors import GlinerExtractor
from strutex.schemas import INVOICE_GENERIC

# Fast local pre-extraction
extractor = GlinerExtractor(labels=["invoice_number", "date", "amount"])
pre_extracted = extractor.extract("invoice.pdf")

# LLM refines and validates
processor = DocumentProcessor(provider="gemini")
result = processor.process(
    "invoice.pdf",
    f"Extract invoice. Hints: {pre_extracted}",
    model=INVOICE_GENERIC
)
```

!!! note "Installation"
Install with: `pip install strutex[gliner]`

---

## Auto-Selection

Use `get_extractor()` to automatically select based on MIME type:

```python
from strutex import get_extractor
from strutex.documents import get_mime_type

mime_type = get_mime_type("file.pdf")
extractor = get_extractor(mime_type)
text = extractor.extract("file.pdf")
```

---

## Creating Custom Extractors

```python
from strutex.plugins import Extractor

class XMLExtractor(Extractor, name="xml"):
    mime_types = ["application/xml", "text/xml"]

    def extract(self, file_path: str) -> str:
        import xml.etree.ElementTree as ET
        tree = ET.parse(file_path)
        return ET.tostring(tree.getroot(), encoding="unicode")

    def can_handle(self, mime_type: str) -> bool:
        return mime_type in self.mime_types
```

---

## API Reference

::: strutex.extractors.PDFExtractor
options:
show_root_heading: true

::: strutex.extractors.ImageExtractor
options:
show_root_heading: true

::: strutex.extractors.ExcelExtractor
options:
show_root_heading: true
