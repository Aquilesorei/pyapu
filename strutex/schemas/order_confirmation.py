"""
Order Confirmation schemas for structured extraction.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class OrderItem(BaseModel):
    """Single line item in an order confirmation."""
    position: Optional[int] = Field(None, description="Item position number (1, 2, 3...)")
    description: str = Field(..., description="Description of goods or services")
    quantity: float = Field(..., description="Quantity ordered")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    total_price: Optional[float] = Field(None, description="Total line item price")
    article_number: Optional[str] = Field(None, description="Vendor article/part number")
    delivery_date: Optional[str] = Field(None, description="Specific delivery date for this item")

class OrderConfirmation(BaseModel):
    """
    Order Confirmation / Quotation schema.
    
    Represents a formal confirmation of an order or a sales quotation.
    """
    
    # IDs
    quotation_number: Optional[str] = Field(None, description="Quotation or Order Confirmation number")
    order_reference: Optional[str] = Field(None, description="Buyer's PO number or reference")
    customer_number: Optional[str] = Field(None, description="Customer ID with vendor")
    
    # Dates
    order_date: Optional[str] = Field(None, description="Date purchase order was placed")
    confirmation_date: Optional[str] = Field(None, description="Date confirmation was issued")
    delivery_date: Optional[str] = Field(None, description="Expected delivery date/time")
    valid_until: Optional[str] = Field(None, description="Quotation validity expiry date")
    
    # Parties
    vendor: str = Field(..., description="Selling company name")
    vendor_address: Optional[str] = Field(None, description="Full vendor address and contact details")
    buyer: str = Field(..., description="Buying company name")
    buyer_address: Optional[str] = Field(None, description="Full buyer billing address")
    shipping_address: Optional[str] = Field(None, description="Delivery address if different")
    
    # Items
    items: List[OrderItem] = Field(default_factory=list, description="List of ordered items")
    
    # Financials
    currency: str = Field("EUR", description="Currency code (EUR, USD, etc.)")
    subtotal: Optional[float] = Field(None, description="Net amount before tax")
    vat: Optional[float] = Field(None, description="VAT/Tax amount")
    shipping_cost: Optional[float] = Field(None, description="Shipping charges")
    total: float = Field(..., description="Grand total amount")
    
    # Terms
    payment_terms: Optional[str] = Field(None, description="Payment terms info")
    delivery_terms: Optional[str] = Field(None, description="Incoterms or delivery conditions")

# Convenient instance
ORDER_CONFIRMATION = OrderConfirmation
