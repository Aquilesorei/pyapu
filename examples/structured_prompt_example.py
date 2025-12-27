"""
Example: Using StructuredPrompt Builder

Demonstrates the fluent API for building organized extraction prompts.
The variadic argument support allows adding multiple rules in a single call.
"""

from strutex import StructuredPrompt, DocumentProcessor, Object, String, Number, Array

# ============================================================================
# 1. Basic Usage - Simple Invoice Extraction
# ============================================================================

basic_prompt = (
    StructuredPrompt()
    .add_general_rule(
        "Extract data exactly as shown in the document.",
        "Do not invent or guess missing values.",
        "Use null for fields that cannot be found."
    )
    .add_field_rule("invoice_number", "Usually starts with 'INV-' or similar prefix.")
    .add_field_rule("total", "Must be a numeric value.", "Exclude tax if shown separately.")
    .add_output_guideline("Return valid JSON only.")
    .compile()
)

print("=== Basic Prompt ===")
print(basic_prompt)
print()

# ============================================================================
# 2. Critical Fields - German Invoice Example
# ============================================================================

german_invoice_prompt = (
    StructuredPrompt(persona="Du bist ein präziser KI-Datenextraktions-Assistent.")
    .add_general_rule(
        "Strikte Datentreue: Erfinde keine Werte.",
        "Datumsformat: DD.MM.YYYY",
        "Ignoriere handschriftliche Notizen."
    )
    .add_field_rule(
        "artikelnummer",
        "Muss 8 Ziffern haben.",
        "Ignoriere Lieferantencodes wie 'ROVJ...'.",
        critical=True  # Marks as **CRITICAL**
    )
    .add_field_rule(
        "menge",
        "Numerischer Wert ohne Einheit.",
        critical=True
    )
    .add_field_rule(
        "einzelpreis",
        "Dezimalzahl mit Punkt als Trennzeichen.",
        "Beispiel: 123.45"
    )
    .add_output_guideline(
        "Gib nur gültiges JSON zurück.",
        "Keine Markdown-Codeblöcke."
    )
    .compile()
)

print("=== German Invoice Prompt ===")
print(german_invoice_prompt)
print()

# ============================================================================
# 3. Full Processing Example
# ============================================================================

def process_invoice_example():
    """
    Complete example combining StructuredPrompt with DocumentProcessor.
    """
    # Define schema
    invoice_schema = Object(
        description="Invoice data extraction",
        properties={
            "invoice_number": String(description="The invoice ID"),
            "date": String(description="Invoice date in DD.MM.YYYY format"),
            "vendor": String(description="Vendor/supplier name"),
            "total": Number(description="Total amount"),
            "items": Array(
                items=Object(
                    properties={
                        "description": String,
                        "quantity": Number,
                        "unit_price": Number,
                        "line_total": Number,
                    }
                )
            )
        }
    )

    # Build prompt
    prompt = (
        StructuredPrompt()
        .add_general_rule(
            "Extract all visible invoice data.",
            "Dates must be in DD.MM.YYYY format.",
            "Numbers should use dot as decimal separator."
        )
        .add_field_rule(
            "invoice_number",
            "Look for 'Rechnungsnummer', 'Invoice No', or similar labels.",
            critical=True
        )
        .add_field_rule(
            "total",
            "This is the final payable amount.",
            "Include VAT if not shown separately."
        )
        .add_field_rule(
            "items",
            "Extract all line items from the invoice table.",
            "Each item must have description, quantity, and prices."
        )
        .add_output_guideline(
            "Return valid JSON matching the provided schema.",
            "Use null for any field that cannot be determined."
        )
        .compile()
    )

    print("=== Full Processing Prompt ===")
    print(prompt)
    print()

    # Uncomment to actually process a file:
    # processor = DocumentProcessor(provider="gemini")
    # result = processor.process("invoice.pdf", prompt, invoice_schema)
    # print(result)


# ============================================================================
# 4. Prompt can also be used as string directly
# ============================================================================

prompt_obj = (
    StructuredPrompt()
    .add_general_rule("Rule 1", "Rule 2")
    .add_field_rule("field1", "Must be valid")
)

# These are equivalent:
print("=== String Conversion ===")
print(f"Using compile(): {len(prompt_obj.compile())} chars")
print(f"Using str():     {len(str(prompt_obj))} chars")
print(f"Repr: {repr(prompt_obj)}")
print()


# ============================================================================
# Run examples
# ============================================================================

if __name__ == "__main__":
    process_invoice_example()
