"""
Real Estate Listing Extraction Example

Demonstrates extracting structured data from property listings.
"""

from strutex import DocumentProcessor, Object, String, Number, Array, Boolean


real_estate_schema = Object(
    description="Real estate listing data",
    properties={
        "property_type": String(description="e.g., House, Apartment, Condo"),
        "listing_type": String(description="Sale or Rent"),
        "address": Object(properties={
            "street": String,
            "city": String,
            "state": String,
            "zip_code": String,
            "country": String,
        }),
        "price": Object(properties={
            "amount": Number,
            "currency": String,
            "price_per_sqft": Number,
        }),
        "details": Object(properties={
            "bedrooms": Number,
            "bathrooms": Number,
            "square_feet": Number,
            "lot_size": Number,
            "year_built": Number,
            "stories": Number,
            "garage_spaces": Number,
        }),
        "features": Array(items=String),
        "amenities": Array(items=String),
        "description": String,
        "status": String(description="e.g., Active, Pending, Sold"),
        "days_on_market": Number,
        "mls_number": String,
        "agent": Object(properties={
            "name": String,
            "phone": String,
            "email": String,
            "brokerage": String,
        }),
        "hoa": Object(properties={
            "has_hoa": Boolean,
            "monthly_fee": Number,
        }),
    }
)

real_estate_prompt = """
Extract all property listing information from this document.

Guidelines:
- Extract complete address
- Capture all property details (beds, baths, sqft)
- List all features and amenities
- Include agent/broker information
- Note HOA fees if applicable
"""


def extract_listing(file_path: str):
    processor = DocumentProcessor(provider="gemini")
    return processor.process(file_path, real_estate_prompt, real_estate_schema)


if __name__ == "__main__":
    print("Real Estate Listing Extraction Example")
    print(f"Schema fields: {len(real_estate_schema.properties)}")
