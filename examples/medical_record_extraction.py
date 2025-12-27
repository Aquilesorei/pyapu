"""
Medical Record Extraction Example

Demonstrates extracting structured data from medical documents.
"""

from strutex import DocumentProcessor, Object, String, Number, Array


medical_schema = Object(
    description="Medical record data",
    properties={
        "patient": Object(properties={
            "name": String,
            "date_of_birth": String,
            "gender": String,
            "patient_id": String,
        }),
        "visit_date": String,
        "provider": Object(properties={
            "name": String,
            "specialty": String,
            "facility": String,
        }),
        "chief_complaint": String,
        "diagnosis": Array(
            items=Object(properties={
                "code": String(description="ICD code if available"),
                "description": String,
            })
        ),
        "medications": Array(
            items=Object(properties={
                "name": String,
                "dosage": String,
                "frequency": String,
            })
        ),
        "vital_signs": Object(properties={
            "blood_pressure": String,
            "heart_rate": Number,
            "temperature": Number,
            "weight": Number,
        }),
        "lab_results": Array(
            items=Object(properties={
                "test": String,
                "value": String,
                "unit": String,
                "reference_range": String,
            })
        ),
        "treatment_plan": String,
        "follow_up": String,
    }
)

medical_prompt = """
Extract patient and clinical information from this medical record.

Guidelines:
- Extract patient demographics
- List all diagnoses with codes if available
- Capture all medications with dosages
- Include vital signs and lab results
- Note treatment plans and follow-up instructions

IMPORTANT: Handle this data with appropriate care for privacy.
"""


def extract_medical_record(file_path: str):
    processor = DocumentProcessor(provider="gemini")
    return processor.process(file_path, medical_prompt, medical_schema)


if __name__ == "__main__":
    print("Medical Record Extraction Example")
    print(f"Schema fields: {len(medical_schema.properties)}")
