"""
Resume/CV Extraction Example

Demonstrates extracting structured data from resumes and CVs.
"""

from strutex import DocumentProcessor, Object, String, Number, Array


# Define resume schema
resume_schema = Object(
    description="Structured resume data",
    properties={
        "name": String(description="Full name of the candidate"),
        "email": String(description="Email address"),
        "phone": String(description="Phone number"),
        "summary": String(description="Professional summary or objective"),
        "experience": Array(
            description="Work experience entries",
            items=Object(properties={
                "company": String,
                "title": String(description="Job title"),
                "start_date": String,
                "end_date": String(description="End date or 'Present'"),
                "responsibilities": Array(items=String),
            })
        ),
        "education": Array(
            description="Educational background",
            items=Object(properties={
                "institution": String,
                "degree": String,
                "field": String(description="Field of study"),
                "graduation_year": Number,
            })
        ),
        "skills": Array(
            description="Technical and soft skills",
            items=String
        ),
        "certifications": Array(
            description="Professional certifications",
            items=Object(properties={
                "name": String,
                "issuer": String,
                "date": String,
            })
        ),
    }
)

# Extraction prompt for resumes
resume_prompt = """
Extract all information from this resume/CV document.

Guidelines:
- Extract the full name, not nicknames
- Normalize phone numbers to include country code if visible
- For ongoing positions, use "Present" as end_date
- List skills as individual items, not comma-separated strings
- Include all certifications with their issuing organizations
"""


def extract_resume(file_path: str):
    """
    Extract structured data from a resume PDF.
    
    Args:
        file_path: Path to the resume PDF
        
    Returns:
        Structured resume data
    """
    processor = DocumentProcessor(provider="gemini")
    
    result = processor.process(
        file_path=file_path,
        prompt=resume_prompt,
        schema=resume_schema
    )
    
    return result


def validate_resume(data: dict):
    """Validate extracted resume data."""
    from strutex import SchemaValidator, ValidationChain
    
    chain = ValidationChain([
        SchemaValidator(),
    ])
    
    result = chain.validate(data, resume_schema)
    return result


if __name__ == "__main__":
    # Example usage (requires actual resume file)
    print("Resume Extraction Example")
    print("=" * 50)
    print("\nSchema fields:")
    for field in resume_schema.properties.keys():
        print(f"  - {field}")
    
    print("\nTo use:")
    print('  result = extract_resume("path/to/resume.pdf")')
