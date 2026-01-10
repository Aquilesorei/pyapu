"""
Sum validator - verifies line items sum to total.
"""

from typing import Any, Dict, List, Optional

from ..plugins.base import Validator, ValidationResult
from ..exceptions import SumValidationError


class SumValidator(Validator, name="sum"):
    """
    Validates that line item amounts sum to the stated total.
    
    Common use case: Invoice validation where item totals should 
    match the invoice total.
    
    Attributes:
        items_field: Field name containing the list of items
        amount_field: Field name in each item containing the amount
        total_field: Field name containing the expected total
        tolerance: Acceptable difference (for floating point comparison)
        strict: If True, fail when required fields are missing
    """
    
    priority = 60
    
    def __init__(
        self,
        items_field: str = "items",
        amount_field: str = "amount",
        total_field: str = "total",
        tolerance: float = 0.01,
        strict: bool = False
    ):
        """
        Initialize the sum validator.
        
        Args:
            items_field: Name of the field containing line items
            amount_field: Name of the amount field in each item
            total_field: Name of the total field
            tolerance: Maximum acceptable difference
            strict: If True, fail validation when items or total are missing
        """
        self.items_field = items_field
        self.amount_field = amount_field
        self.total_field = total_field
        self.tolerance = tolerance
        self.strict = strict
    
    def validate(
        self,
        data: Dict[str, Any],
        schema: Any = None,
        source_text: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate that line items sum to the total.
        
        Args:
            data: The extracted data to validate
            schema: Not used by this validator
            
        Returns:
            ValidationResult indicating if sums match
        """
        issues = []
        
        # Get items and total
        items = data.get(self.items_field, [])
        total = data.get(self.total_field)
        
        # Handle missing fields
        if not items or total is None:
            if self.strict:
                missing = []
                if not items:
                    missing.append(f"'{self.items_field}' (line items)")
                if total is None:
                    missing.append(f"'{self.total_field}'")
                issues.append(f"Missing required fields: {', '.join(missing)}")
                return ValidationResult(valid=False, data=data, issues=issues)
            # Non-strict mode: skip validation when fields are missing
            return ValidationResult(valid=True, data=data)
        
        # Calculate sum of items
        try:
            items_sum = sum(
                float(item.get(self.amount_field, 0)) 
                for item in items 
                if isinstance(item, dict)
            )
        except (TypeError, ValueError) as e:
            issues.append(f"Could not calculate sum: {e}")
            return ValidationResult(valid=False, data=data, issues=issues)
        
        # Compare with tolerance
        try:
            total_float = float(total)
        except (TypeError, ValueError):
            issues.append(f"Total field is not a number: {total}")
            return ValidationResult(valid=False, data=data, issues=issues)
        
        difference = abs(items_sum - total_float)
        
        if difference > self.tolerance:
            issues.append(
                f"Sum mismatch: items sum to {items_sum:.2f}, "
                f"but total is {total_float:.2f} "
                f"(difference: {difference:.2f})"
            )
            return ValidationResult(valid=False, data=data, issues=issues)
        
        return ValidationResult(valid=True, data=data)
