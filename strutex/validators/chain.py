"""
Validation chain for composing multiple validators.
"""

from typing import Any, Dict, List, Optional

from ..plugins.base import Validator, ValidationResult


class ValidationChain:
    """
    Composes multiple validators into a sequential chain.
    
    Validators run in order. If any validator fails (in strict mode),
    the chain stops and returns the failure. In lenient mode, all
    validators run and issues are collected.
    
    Example:
        ```python
        chain = ValidationChain([
            SchemaValidator(),
            SumValidator(tolerance=0.01),
            DateValidator(date_fields=["invoice_date"]),
        ])
        
        result = chain.validate(data, schema)
        if not result.valid:
            print(result.issues)
        ```
    """
    
    def __init__(
        self,
        validators: List[Validator],
        strict: bool = True
    ):
        """
        Initialize the validation chain.
        
        Args:
            validators: List of validators to run in order
            strict: If True, stop on first failure. If False, collect all issues.
        """
        self.validators = validators
        self.strict = strict
    
    def validate(
        self,
        data: Dict[str, Any],
        schema=None,
        source_text: Optional[str] = None
    ) -> ValidationResult:
        """
        Run all validators in the chain.
        
        Args:
            data: The data to validate
            schema: Optional schema to pass to validators
            
        Returns:
            Combined ValidationResult from all validators
        """
        all_issues: List[str] = []
        current_data = data
        
        for validator in self.validators:
            result = validator.validate(current_data, schema, source_text=source_text)
            
            if not result.valid:
                all_issues.extend(result.issues)
                
                if self.strict:
                    return ValidationResult(
                        valid=False,
                        data=current_data,
                        issues=all_issues
                    )
            
            # Use possibly modified data for next validator
            current_data = result.data
        
        return ValidationResult(
            valid=len(all_issues) == 0,
            data=current_data,
            issues=all_issues
        )
    
    def add(self, validator: Validator) -> "ValidationChain":
        """
        Add a validator to the chain.
        
        Args:
            validator: The validator to add
            
        Returns:
            Self for method chaining
        """
        self.validators.append(validator)
        return self
