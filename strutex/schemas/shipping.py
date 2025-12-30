"""
Shipping document schemas for structured extraction.

Covers bills of lading and shipping documentation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Container(BaseModel):
    """Shipping container details."""
    container_number: str = Field(..., description="Container number/ID")
    seal_number: Optional[str] = Field(None, description="Seal number")
    container_type: Optional[str] = Field(None, description="Container type (20GP, 40HC, etc.)")
    weight: Optional[float] = Field(None, description="Gross weight")
    weight_unit: Optional[str] = Field("KG", description="Weight unit (KG, LBS)")


class Cargo(BaseModel):
    """Cargo/goods details."""
    description: str = Field(..., description="Description of goods")
    quantity: Optional[float] = Field(None, description="Number of packages/pieces")
    package_type: Optional[str] = Field(None, description="Package type (cartons, pallets, etc.)")
    gross_weight: Optional[float] = Field(None, description="Gross weight")
    net_weight: Optional[float] = Field(None, description="Net weight")
    weight_unit: Optional[str] = Field("KG", description="Weight unit")
    volume: Optional[float] = Field(None, description="Volume/measurement")
    volume_unit: Optional[str] = Field("CBM", description="Volume unit")
    marks_and_numbers: Optional[str] = Field(None, description="Shipping marks")
    hs_code: Optional[str] = Field(None, description="HS/tariff code")


class BillOfLading(BaseModel):
    """
    Bill of Lading (B/L) schema for ocean freight.
    
    Example:
        >>> from strutex import DocumentProcessor
        >>> from strutex.schemas import BILL_OF_LADING
        >>> 
        >>> processor = DocumentProcessor()
        >>> bol = processor.process("bl.pdf", "Extract B/L", model=BILL_OF_LADING)
        >>> print(f"B/L #{bol.bl_number}: {bol.port_of_loading} -> {bol.port_of_discharge}")
    """
    
    # Document identification
    bl_number: str = Field(..., description="Bill of Lading number")
    bl_type: Optional[str] = Field(None, description="Type (Original, Copy, Sea Waybill, etc.)")
    bl_date: Optional[str] = Field(None, description="Issue date")
    
    # Parties
    shipper: Optional[str] = Field(None, description="Shipper/exporter name and address")
    consignee: Optional[str] = Field(None, description="Consignee name and address")
    notify_party: Optional[str] = Field(None, description="Notify party name and address")
    
    # Carrier
    carrier: Optional[str] = Field(None, description="Shipping line/carrier name")
    vessel_name: Optional[str] = Field(None, description="Vessel/ship name")
    voyage_number: Optional[str] = Field(None, description="Voyage number")
    
    # Routing
    port_of_loading: Optional[str] = Field(None, description="Port of loading (POL)")
    port_of_discharge: Optional[str] = Field(None, description="Port of discharge (POD)")
    place_of_receipt: Optional[str] = Field(None, description="Place of receipt")
    place_of_delivery: Optional[str] = Field(None, description="Final place of delivery")
    
    # Dates
    shipped_on_board_date: Optional[str] = Field(None, description="On-board date")
    estimated_arrival: Optional[str] = Field(None, description="ETA at discharge port")
    
    # Cargo
    cargo: List[Cargo] = Field(
        default_factory=list,
        description="Cargo/goods details"
    )
    
    # Containers
    containers: List[Container] = Field(
        default_factory=list,
        description="Container details"
    )
    
    # Totals
    total_packages: Optional[int] = Field(None, description="Total number of packages")
    total_gross_weight: Optional[float] = Field(None, description="Total gross weight")
    total_volume: Optional[float] = Field(None, description="Total volume/measurement")
    
    # Freight
    freight_terms: Optional[str] = Field(None, description="Freight terms (Prepaid, Collect)")
    freight_amount: Optional[float] = Field(None, description="Freight charges")
    
    # References
    booking_number: Optional[str] = Field(None, description="Booking reference number")
    export_reference: Optional[str] = Field(None, description="Shipper's export reference")
    lc_number: Optional[str] = Field(None, description="Letter of credit number")


# Convenient schema instance
BILL_OF_LADING = BillOfLading
