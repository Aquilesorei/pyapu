"""
Research Paper Extraction Example

Demonstrates extracting structured metadata from academic papers.
"""

from strutex import DocumentProcessor, Object, String, Number, Array


# Define research paper schema
paper_schema = Object(
    description="Academic paper metadata",
    properties={
        "title": String(description="Paper title"),
        "authors": Array(
            description="List of authors",
            items=Object(properties={
                "name": String,
                "affiliation": String(description="University or organization"),
                "email": String,
            })
        ),
        "abstract": String(description="Paper abstract"),
        "keywords": Array(
            description="Keywords or topics",
            items=String
        ),
        "publication_date": String(description="Publication date"),
        "journal": String(description="Journal or conference name"),
        "doi": String(description="Digital Object Identifier"),
        "volume": String,
        "issue": String,
        "pages": String(description="Page range, e.g., '123-145'"),
        "sections": Array(
            description="Main sections of the paper",
            items=Object(properties={
                "title": String,
                "summary": String(description="Brief summary of section content"),
            })
        ),
        "references_count": Number(description="Number of references cited"),
        "funding": Array(
            description="Funding sources",
            items=String
        ),
    }
)

# Extraction prompt for research papers
paper_prompt = """
Extract metadata and key information from this academic paper.

Guidelines:
- Extract all authors with their affiliations if available
- Capture the full abstract
- Identify main section headings (Introduction, Methods, Results, etc.)
- Count the total number of references
- Extract DOI if present
- List any funding acknowledgments
"""


def extract_paper(file_path: str):
    """
    Extract structured metadata from an academic paper.
    
    Args:
        file_path: Path to the paper PDF
        
    Returns:
        Structured paper metadata
    """
    processor = DocumentProcessor(provider="gemini")
    
    result = processor.process(
        file_path=file_path,
        prompt=paper_prompt,
        schema=paper_schema
    )
    
    return result


def validate_paper(data: dict):
    """Validate extracted paper data."""
    from strutex import SchemaValidator, DateValidator, ValidationChain
    
    chain = ValidationChain([
        SchemaValidator(),
        DateValidator(date_fields=["publication_date"]),
    ])
    
    result = chain.validate(data, paper_schema)
    return result


if __name__ == "__main__":
    print("Research Paper Extraction Example")
    print("=" * 50)
    print("\nSchema fields:")
    for field in paper_schema.properties.keys():
        print(f"  - {field}")
    
    print("\nTo use:")
    print('  result = extract_paper("path/to/paper.pdf")')
