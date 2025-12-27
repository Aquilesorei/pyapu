# Built-in Schemas

strutex includes ready-to-use Pydantic schemas for common document types. Use these directly with `DocumentProcessor` for instant structured extraction.

---

## Quick Start

```python
from strutex import DocumentProcessor
from strutex.schemas import INVOICE_US

processor = DocumentProcessor(provider="gemini")
invoice = processor.process(
    "invoice.pdf",
    "Extract invoice details",
    model=INVOICE_US
)

print(f"Invoice #{invoice.invoice_number}")
print(f"Total: ${invoice.total}")
print(f"Items: {len(invoice.line_items)}")
```

---

## Available Schemas

### Invoices

| Schema            | Description              | Key Fields                                          |
| ----------------- | ------------------------ | --------------------------------------------------- |
| `INVOICE_GENERIC` | Universal invoice format | invoice_number, vendor, customer, line_items, total |
| `INVOICE_US`      | US-style with sales tax  | + sales_tax, state_tax_rate, ein                    |
| `INVOICE_EU`      | EU-style with VAT        | + vat_number, vat_rate, reverse_charge              |

```python
from strutex.schemas import INVOICE_GENERIC, INVOICE_US, INVOICE_EU
```

### Receipts

| Schema    | Description                | Key Fields                                                 |
| --------- | -------------------------- | ---------------------------------------------------------- |
| `RECEIPT` | Retail/restaurant receipts | merchant_name, items, subtotal, tax, total, payment_method |

```python
from strutex.schemas import RECEIPT

receipt = processor.process("receipt.jpg", "Extract receipt", model=RECEIPT)
print(f"Store: {receipt.merchant_name}, Total: ${receipt.total}")
```

### Purchase Orders

| Schema           | Description         | Key Fields                                                 |
| ---------------- | ------------------- | ---------------------------------------------------------- |
| `PURCHASE_ORDER` | B2B purchase orders | po_number, vendor_name, line_items, ship_to, payment_terms |

```python
from strutex.schemas import PURCHASE_ORDER
```

### Order Confirmations

| Schema               | Description                  | Key Fields                                               |
| -------------------- | ---------------------------- | -------------------------------------------------------- |
| `ORDER_CONFIRMATION` | Quotations / Order Responses | quotation_number, vendor, buyer, items, delivery, totals |

```python
from strutex.schemas import ORDER_CONFIRMATION
```

### Shipping Documents

| Schema           | Description       | Key Fields                                                                           |
| ---------------- | ----------------- | ------------------------------------------------------------------------------------ |
| `BILL_OF_LADING` | Ocean freight B/L | bl_number, shipper, consignee, containers, cargo, port_of_loading, port_of_discharge |

**Container Fields:** `container_number`, `seal_number`, `type`, `weight`
**Cargo Fields:** `description`, `quantity`, `gross_weight`, `volume`, `hs_code`, `marks`

```python
from strutex.schemas import BILL_OF_LADING

bol = processor.process("bl.pdf", "Extract B/L", model=BILL_OF_LADING)
print(f"{bol.port_of_loading} → {bol.port_of_discharge}")
```

### Financial Documents

| Schema           | Description             | Key Fields                                                     |
| ---------------- | ----------------------- | -------------------------------------------------------------- |
| `BANK_STATEMENT` | Bank account statements | account_number, opening_balance, closing_balance, transactions |

```python
from strutex.schemas import BANK_STATEMENT
```

### Resumes/CVs

| Schema   | Description          | Key Fields                                                      |
| -------- | -------------------- | --------------------------------------------------------------- |
| `RESUME` | Professional resumes | name, email, skills, work_experience, education, certifications |

```python
from strutex.schemas import RESUME

resume = processor.process("resume.pdf", "Extract resume", model=RESUME)
print(f"{resume.name}: {len(resume.work_experience)} positions")
```

### Legal Documents

| Schema            | Description        | Key Fields                                                   |
| ----------------- | ------------------ | ------------------------------------------------------------ |
| `CONTRACT_CLAUSE` | Contract key terms | title, parties, effective_date, payment_terms, governing_law |

```python
from strutex.schemas import CONTRACT_CLAUSE
```

---

## Extending Schemas

Create custom schemas by inheriting from built-in ones:

```python
from strutex.schemas import InvoiceGeneric
from pydantic import Field

class MyInvoice(InvoiceGeneric):
    """Custom invoice with company-specific fields."""
    internal_code: str = Field(..., description="Internal tracking code")
    department: str = Field(None, description="Department to charge")

# Use your custom schema
result = processor.process("invoice.pdf", "Extract invoice", model=MyInvoice)
```

---

## Schema Reference

### InvoiceGeneric Fields

| Field            | Type   | Description         |
| ---------------- | ------ | ------------------- |
| `invoice_number` | str    | Invoice number/ID   |
| `invoice_date`   | str?   | Invoice date        |
| `due_date`       | str?   | Payment due date    |
| `vendor`         | Party? | Seller information  |
| `customer`       | Party? | Buyer information   |
| `line_items`     | list   | List of line items  |
| `subtotal`       | float? | Subtotal before tax |
| `tax_amount`     | float? | Tax amount          |
| `total`          | float  | Grand total         |
| `payment_terms`  | str?   | Payment terms       |

### Receipt Fields

| Field            | Type   | Description                |
| ---------------- | ------ | -------------------------- |
| `merchant_name`  | str    | Store name                 |
| `receipt_number` | str?   | Receipt/transaction number |
| `date`           | str?   | Transaction date           |
| `items`          | list   | Purchased items            |
| `subtotal`       | float? | Before tax                 |
| `tax`            | float? | Tax amount                 |
| `total`          | float  | Total paid                 |
| `payment_method` | str?   | Cash, Card, etc.           |

### BillOfLading Fields

| Field               | Type | Description            |
| ------------------- | ---- | ---------------------- |
| `bl_number`         | str  | B/L number             |
| `shipper`           | str? | Shipper name/address   |
| `consignee`         | str? | Consignee name/address |
| `carrier`           | str? | Shipping line          |
| `vessel_name`       | str? | Ship name              |
| `port_of_loading`   | str? | POL                    |
| `port_of_discharge` | str? | POD                    |
| `containers`        | list | Container details      |
| `cargo`             | list | Cargo details          |

---

## Best Practices

1. **Use specific schemas when possible** - `INVOICE_US` over `INVOICE_GENERIC` for better accuracy
2. **Extend for custom fields** - Inherit and add company-specific fields
3. **Validate after extraction** - Use Pydantic's validation:

```python
try:
    invoice = processor.process("doc.pdf", "Extract", model=INVOICE_US)
except ValidationError as e:
    print(f"Extraction incomplete: {e}")
```
