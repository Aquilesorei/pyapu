"""
Simple invoice extraction demo using strutex.

This shows the simplest way to extract structured data from a PDF.
"""

import os
import sys

from dotenv import load_dotenv

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strutex import extract, DocumentProcessor
from strutex import GeminiProvider
from strutex.schemas import INVOICE_GENERIC

# Get the directory of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(SCRIPT_DIR, "order.pdf")
load_dotenv()
# Option 1: One-liner with extract() - uses default gemini provider
# result = extract(PDF_PATH, model=INVOICE_GENERIC)

# Option 2: Explicit provider instance (recommended for production)
processor = DocumentProcessor(
    provider=GeminiProvider(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini-2.5-flash"
    )
)

invoice = processor.process(
    file_path=PDF_PATH,
    prompt="Extract all invoice details from this document.",
    model=INVOICE_GENERIC
)

# Print results
print("=" * 60)
print("INVOICE EXTRACTION RESULT")
print("=" * 60)

print(f"\n📄 Invoice Number: {invoice.invoice_number}")
print(f"📅 Date: {invoice.invoice_date}")
print(f"📅 Due Date: {invoice.due_date}")

if invoice.vendor:
    print(f"\n🏢 Vendor: {invoice.vendor.name}")
    if invoice.vendor.address:
        print(f"   Address: {invoice.vendor.address.street}, {invoice.vendor.address.city}")

if invoice.customer:
    print(f"\n👤 Customer: {invoice.customer.name}")
    if invoice.customer.address:
        print(f"   Address: {invoice.customer.address.street}, {invoice.customer.address.city}")

print(f"\n💰 Currency: {invoice.currency}")
if invoice.subtotal:
    print(f"   Subtotal: {invoice.subtotal}")
if invoice.tax_amount:
    print(f"   Tax: {invoice.tax_amount}")
print(f"   TOTAL: {invoice.total}")

if invoice.line_items:
    print(f"\n📋 Line Items ({len(invoice.line_items)}):")
    for i, item in enumerate(invoice.line_items, 1):
        qty = f"x{item.quantity}" if item.quantity else ""
        print(f"   {i}. {item.description} {qty} = {item.amount}")

if invoice.payment_terms:
    print(f"\n💳 Payment Terms: {invoice.payment_terms}")

if invoice.notes:
    print(f"\n📝 Notes: {invoice.notes}")

print("\n" + "=" * 60)
