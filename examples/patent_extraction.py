"""
Patent Document Extraction Example

Demonstrates extracting structured data from patent documents.
"""

from strutex import DocumentProcessor, Object, String, Number, Array


patent_schema = Object(
    description="Patent document data",
    properties={
        "patent_number": String,
        "application_number": String,
        "title": String,
        "abstract": String,
        "inventors": Array(
            items=Object(properties={
                "name": String,
                "city": String,
                "country": String,
            })
        ),
        "assignee": Object(properties={
            "name": String,
            "city": String,
            "country": String,
        }),
        "filing_date": String,
        "publication_date": String,
        "grant_date": String,
        "priority_date": String,
        "classifications": Array(
            items=Object(properties={
                "type": String(description="IPC, CPC, etc."),
                "code": String,
            })
        ),
        "claims_count": Number,
        "independent_claims": Array(items=String),
        "cited_patents": Array(items=String),
        "cited_by_count": Number,
        "status": String,
        "expiration_date": String,
    }
)

patent_prompt = """
Extract patent information from this document.

Guidelines:
- Extract patent and application numbers
- List all inventors with locations
- Capture filing, publication, and grant dates
- Extract classification codes
- Include main claims
"""


def extract_patent(file_path: str):
    processor = DocumentProcessor(provider="gemini")
    return processor.process(file_path, patent_prompt, patent_schema)


if __name__ == "__main__":
    print("Patent Extraction Example")
    print(f"Schema fields: {len(patent_schema.properties)}")
