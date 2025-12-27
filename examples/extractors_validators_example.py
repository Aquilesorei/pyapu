"""
Extractors and Validators Example

Demonstrates using strutex extractors and validators for document processing.
"""

from strutex import (
    PDFExtractor,
    ImageExtractor,
    ExcelExtractor,
    get_extractor,
    SchemaValidator,
    SumValidator,
    DateValidator,
    ValidationChain,
    Object,
    String,
    Number,
    Array,
)


# =============================================================================
# EXTRACTORS - Convert documents to text
# =============================================================================

def extractor_examples():
    """Demonstrate extractor usage."""
    
    # 1. Direct usage
    pdf_extractor = PDFExtractor()
    # text = pdf_extractor.extract("invoice.pdf")
    
    # 2. Auto-select by MIME type
    extractor = get_extractor("application/pdf")
    print(f"Selected extractor: {extractor.__class__.__name__}")
    
    # 3. Check capabilities
    print(f"PDFExtractor can handle PDF: {pdf_extractor.can_handle('application/pdf')}")
    print(f"PDFExtractor can handle PNG: {pdf_extractor.can_handle('image/png')}")
    
    # 4. Image extractor (requires OCR)
    image_extractor = ImageExtractor()
    print(f"OCR available: {image_extractor.health_check()}")


# =============================================================================
# VALIDATORS - Check output quality
# =============================================================================

def validator_examples():
    """Demonstrate validator usage with diverse document types."""
    
    # Example 1: Invoice data
    invoice_data = {
        "invoice_number": "INV-2024-001",
        "invoice_date": "2024-01-15",
        "items": [
            {"description": "Widget A", "amount": 100.00},
            {"description": "Widget B", "amount": 50.00},
        ],
        "total": 150.00
    }
    
    # Example 2: Resume/CV data
    resume_data = {
        "name": "John Smith",
        "email": "john@example.com",
        "experience": [
            {"company": "Acme Corp", "role": "Engineer", "years": 3},
            {"company": "Tech Inc", "role": "Senior Engineer", "years": 2},
        ],
        "skills": ["Python", "Machine Learning", "Data Analysis"]
    }
    
    # Example 3: Research paper metadata
    paper_data = {
        "title": "Advances in NLP",
        "authors": ["Alice Brown", "Bob Johnson"],
        "publication_date": "2024-03-20",
        "keywords": ["NLP", "transformers", "attention"],
        "abstract": "This paper explores..."
    }
    
    # Example 4: Product specification
    product_data = {
        "product_name": "Smart Widget Pro",
        "sku": "SWP-2024",
        "dimensions": {"width": 10.5, "height": 5.2, "depth": 2.1},
        "weight_kg": 0.35,
        "price": 49.99
    }
    
    print("Validating diverse document types:")
    
    # Schema validation works for any structure
    schema_validator = SchemaValidator()
    
    # Invoice schema
    invoice_schema = Object(properties={
        "invoice_number": String,
        "total": Number,
    })
    result = schema_validator.validate(invoice_data, invoice_schema)
    print(f"  Invoice valid: {result.valid}")
    
    # Resume schema  
    resume_schema = Object(properties={
        "name": String,
        "email": String,
        "skills": Array(items=String),
    })
    result = schema_validator.validate(resume_data, resume_schema)
    print(f"  Resume valid: {result.valid}")
    
    # Date validation works for any date field
    date_validator = DateValidator()
    result = date_validator.validate(paper_data)
    print(f"  Paper dates valid: {result.valid}")
    
    # Sum validation for financial documents
    sum_validator = SumValidator()
    result = sum_validator.validate(invoice_data)
    print(f"  Invoice sum valid: {result.valid}")


# =============================================================================
# VALIDATION FAILURE EXAMPLES
# =============================================================================

def validation_failure_examples():
    """Show how validation catches errors."""
    
    # Data with sum mismatch
    bad_data = {
        "items": [
            {"amount": 100.00},
            {"amount": 50.00},
        ],
        "total": 200.00  # Wrong! Should be 150
    }
    
    sum_validator = SumValidator()
    result = sum_validator.validate(bad_data)
    
    print(f"\nSum validation failed: {not result.valid}")
    print(f"Issue: {result.issues[0]}")
    
    # Data with invalid date
    bad_date_data = {
        "invoice_date": "invalid-date",
    }
    
    date_validator = DateValidator()
    result = date_validator.validate(bad_date_data)
    
    print(f"\nDate validation failed: {not result.valid}")
    print(f"Issue: {result.issues[0]}")


if __name__ == "__main__":
    print("=" * 60)
    print("EXTRACTOR EXAMPLES")
    print("=" * 60)
    extractor_examples()
    
    print("\n" + "=" * 60)
    print("VALIDATOR EXAMPLES")
    print("=" * 60)
    validator_examples()
    
    print("\n" + "=" * 60)
    print("VALIDATION FAILURE EXAMPLES")
    print("=" * 60)
    validation_failure_examples()
