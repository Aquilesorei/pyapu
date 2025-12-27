"""
Product Specification Extraction Example

Demonstrates extracting structured data from product datasheets and specs.
"""

from strutex import DocumentProcessor, Object, String, Number, Array, Boolean


# Define product specification schema
product_schema = Object(
    description="Product specification data",
    properties={
        "product_name": String(description="Official product name"),
        "sku": String(description="Stock Keeping Unit or product code"),
        "manufacturer": String,
        "category": String(description="Product category"),
        "description": String(description="Product description"),
        "specifications": Object(
            description="Technical specifications",
            properties={
                "dimensions": Object(properties={
                    "width": Number,
                    "height": Number,
                    "depth": Number,
                    "unit": String(description="e.g., mm, cm, inches"),
                }),
                "weight": Object(properties={
                    "value": Number,
                    "unit": String(description="e.g., kg, lbs, g"),
                }),
                "materials": Array(items=String),
                "color": String,
                "power_consumption": String(description="e.g., '50W', '120V AC'"),
            }
        ),
        "features": Array(
            description="Key product features",
            items=String
        ),
        "price": Object(
            description="Pricing information",
            properties={
                "amount": Number,
                "currency": String,
                "msrp": Number(description="Manufacturer suggested retail price"),
            }
        ),
        "availability": Object(properties={
            "in_stock": Boolean,
            "lead_time_days": Number,
            "regions": Array(items=String),
        }),
        "warranty": Object(properties={
            "duration_months": Number,
            "type": String(description="e.g., 'Limited', 'Full'"),
        }),
        "certifications": Array(
            description="Safety and quality certifications",
            items=String
        ),
    }
)

# Extraction prompt for product specs
product_prompt = """
Extract all product specification data from this datasheet.

Guidelines:
- Extract exact measurements with their units
- Capture all technical specifications
- List all features and benefits
- Include pricing if available
- Note any certifications (CE, FCC, UL, etc.)
- Extract warranty information
"""


def extract_product_specs(file_path: str):
    """
    Extract structured specifications from a product datasheet.
    
    Args:
        file_path: Path to the product spec PDF
        
    Returns:
        Structured product data
    """
    processor = DocumentProcessor(provider="gemini")
    
    result = processor.process(
        file_path=file_path,
        prompt=product_prompt,
        schema=product_schema
    )
    
    return result


def validate_product(data: dict):
    """Validate extracted product data."""
    from strutex import SchemaValidator, ValidationChain
    
    chain = ValidationChain([
        SchemaValidator(),
    ])
    
    result = chain.validate(data, product_schema)
    return result


if __name__ == "__main__":
    print("Product Specification Extraction Example")
    print("=" * 50)
    print("\nSchema fields:")
    for field in product_schema.properties.keys():
        print(f"  - {field}")
    
    print("\nTo use:")
    print('  result = extract_product_specs("path/to/datasheet.pdf")')
