"""
Insurance Claim Extraction Example

Demonstrates extracting structured data from insurance claims.
"""

from strutex import DocumentProcessor, Object, String, Number, Array


claim_schema = Object(
    description="Insurance claim data",
    properties={
        "claim_number": String,
        "policy_number": String,
        "claim_type": String(description="e.g., Auto, Health, Property"),
        "status": String,
        "claimant": Object(properties={
            "name": String,
            "policy_holder": String,
            "contact_phone": String,
            "email": String,
            "address": String,
        }),
        "incident": Object(properties={
            "date": String,
            "time": String,
            "location": String,
            "description": String,
            "police_report_number": String,
        }),
        "damages": Array(
            items=Object(properties={
                "item": String,
                "description": String,
                "estimated_cost": Number,
            })
        ),
        "total_claimed": Number,
        "deductible": Number,
        "approved_amount": Number,
        "witnesses": Array(
            items=Object(properties={
                "name": String,
                "contact": String,
            })
        ),
        "adjuster": Object(properties={
            "name": String,
            "phone": String,
        }),
        "documents_submitted": Array(items=String),
        "filing_date": String,
        "resolution_date": String,
    }
)

claim_prompt = """
Extract all information from this insurance claim.

Guidelines:
- Extract claimant and policy details
- Capture incident description and date
- List all damages with estimated costs
- Note claim amounts (claimed, deductible, approved)
- Include adjuster information
"""


def extract_claim(file_path: str):
    processor = DocumentProcessor(provider="gemini")
    return processor.process(file_path, claim_prompt, claim_schema)


if __name__ == "__main__":
    print("Insurance Claim Extraction Example")
    print(f"Schema fields: {len(claim_schema.properties)}")
