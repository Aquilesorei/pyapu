"""
Contract Extraction Example

Demonstrates extracting structured data from legal contracts.
"""

from strutex import DocumentProcessor, Object, String, Number, Array, Boolean


contract_schema = Object(
    description="Legal contract data",
    properties={
        "contract_type": String(description="e.g., NDA, Employment, Sales"),
        "title": String,
        "effective_date": String,
        "expiration_date": String,
        "parties": Array(
            items=Object(properties={
                "name": String,
                "role": String(description="e.g., 'Seller', 'Buyer', 'Employer'"),
                "address": String,
            })
        ),
        "key_terms": Array(
            description="Important contractual terms",
            items=Object(properties={
                "term": String,
                "details": String,
            })
        ),
        "obligations": Array(
            description="Obligations of each party",
            items=Object(properties={
                "party": String,
                "obligation": String,
            })
        ),
        "payment_terms": Object(properties={
            "amount": Number,
            "currency": String,
            "schedule": String,
        }),
        "termination_clause": String,
        "governing_law": String(description="Jurisdiction for disputes"),
        "signatures": Array(
            items=Object(properties={
                "name": String,
                "title": String,
                "date": String,
            })
        ),
    }
)

contract_prompt = """
Extract all key information from this legal contract.

Guidelines:
- Identify all parties and their roles
- Extract important dates (effective, expiration)
- List key terms and obligations
- Capture payment terms if present
- Note the governing law/jurisdiction
"""


def extract_contract(file_path: str):
    processor = DocumentProcessor(provider="gemini")
    return processor.process(file_path, contract_prompt, contract_schema)


if __name__ == "__main__":
    print("Contract Extraction Example")
    print(f"Schema fields: {len(contract_schema.properties)}")
