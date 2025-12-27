"""
Bill of Lading Extraction Example

Demonstrates extracting structured data from shipping documents.
"""

from strutex import DocumentProcessor, Object, String, Number, Array


bol_schema = Object(
    description="Bill of Lading data",
    properties={
        "bol_number": String,
        "booking_number": String,
        "shipper": Object(properties={
            "name": String,
            "address": String,
            "contact": String,
        }),
        "consignee": Object(properties={
            "name": String,
            "address": String,
            "contact": String,
        }),
        "notify_party": Object(properties={
            "name": String,
            "address": String,
        }),
        "vessel_name": String,
        "voyage_number": String,
        "port_of_loading": String,
        "port_of_discharge": String,
        "final_destination": String,
        "containers": Array(
            items=Object(properties={
                "container_number": String,
                "seal_number": String,
                "size": String(description="e.g., 20ft, 40ft"),
                "type": String(description="e.g., Dry, Reefer"),
                "weight_kg": Number,
            })
        ),
        "cargo_description": String,
        "package_count": Number,
        "gross_weight_kg": Number,
        "measurement_cbm": Number,
        "freight_terms": String(description="Prepaid or Collect"),
        "issue_date": String,
        "issue_place": String,
    }
)

bol_prompt = """
Extract all shipping information from this Bill of Lading.

Guidelines:
- Extract shipper and consignee details
- Capture all container numbers and seal numbers
- Note ports of loading and discharge
- Include vessel and voyage information
- Extract cargo descriptions and weights
"""


def extract_bol(file_path: str):
    processor = DocumentProcessor(provider="gemini")
    return processor.process(file_path, bol_prompt, bol_schema)


if __name__ == "__main__":
    print("Bill of Lading Extraction Example")
    print(f"Schema fields: {len(bol_schema.properties)}")
