"""
Tests for validators (date, sum, schema).
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strutex.validators.date import DateValidator
from strutex.validators.sum import SumValidator
from strutex.validators.schema import SchemaValidator
from strutex.types import Object, String, Number, Array, Boolean


class TestDateValidator:
    """Tests for DateValidator."""
    
    def test_valid_iso_date(self):
        """Test ISO format dates pass validation."""
        validator = DateValidator()
        data = {"invoice_date": "2024-01-15"}
        result = validator.validate(data)
        assert result.valid is True
        assert len(result.issues) == 0
    
    def test_valid_european_date(self):
        """Test European format dates pass validation."""
        validator = DateValidator()
        data = {"invoice_date": "15.01.2024"}
        result = validator.validate(data)
        assert result.valid is True
    
    def test_valid_us_date(self):
        """Test US format dates pass validation."""
        validator = DateValidator()
        data = {"due_date": "01/15/2024"}
        result = validator.validate(data)
        assert result.valid is True
    
    def test_invalid_date_format(self):
        """Test invalid date format fails validation."""
        validator = DateValidator()
        data = {"invoice_date": "not-a-date"}
        result = validator.validate(data)
        assert result.valid is False
        assert "invalid date format" in result.issues[0]
    
    def test_year_too_old(self):
        """Test year before min_year fails."""
        validator = DateValidator(min_year=2000)
        data = {"invoice_date": "1999-01-01"}
        result = validator.validate(data)
        assert result.valid is False
        assert "before 2000" in result.issues[0]
    
    def test_year_too_future(self):
        """Test year after max_year fails."""
        validator = DateValidator(max_year=2025)
        data = {"invoice_date": "2030-01-01"}
        result = validator.validate(data)
        assert result.valid is False
        assert "after 2025" in result.issues[0]
    
    def test_auto_detect_date_fields(self):
        """Test auto-detection of date fields."""
        validator = DateValidator()
        data = {
            "invoice_date": "2024-01-15",
            "due_date": "2024-02-15",
            "vendor_name": "ACME"  # Not a date field
        }
        result = validator.validate(data)
        assert result.valid is True
    
    def test_specific_date_fields(self):
        """Test specifying specific date fields."""
        validator = DateValidator(date_fields=["custom_field"])
        data = {
            "custom_field": "2024-01-15",
            "other_date": "invalid"  # Should be ignored
        }
        result = validator.validate(data)
        assert result.valid is True
    
    def test_empty_date_skipped(self):
        """Test empty/null dates are skipped."""
        validator = DateValidator()
        data = {"invoice_date": None, "due_date": ""}
        result = validator.validate(data)
        assert result.valid is True
    
    def test_non_string_date_skipped(self):
        """Test non-string date values are skipped."""
        validator = DateValidator()
        data = {"invoice_date": 12345}
        result = validator.validate(data)
        assert result.valid is True
    
    def test_custom_formats(self):
        """Test custom date formats."""
        validator = DateValidator(formats=["%d %b %Y"])
        data = {"invoice_date": "15 Jan 2024"}
        result = validator.validate(data)
        assert result.valid is True


class TestSumValidator:
    """Tests for SumValidator."""
    
    def test_valid_sum(self):
        """Test items sum matches total."""
        validator = SumValidator()
        data = {
            "items": [
                {"amount": 10.00},
                {"amount": 20.00},
                {"amount": 30.00},
            ],
            "total": 60.00
        }
        result = validator.validate(data)
        assert result.valid is True
    
    def test_sum_mismatch(self):
        """Test items sum does not match total."""
        validator = SumValidator()
        data = {
            "items": [
                {"amount": 10.00},
                {"amount": 20.00},
            ],
            "total": 100.00
        }
        result = validator.validate(data)
        assert result.valid is False
        assert "Sum mismatch" in result.issues[0]
    
    def test_within_tolerance(self):
        """Test sum within tolerance passes."""
        validator = SumValidator(tolerance=0.10)
        data = {
            "items": [{"amount": 10.00}],
            "total": 10.05  # Within 0.10 tolerance
        }
        result = validator.validate(data)
        assert result.valid is True
    
    def test_outside_tolerance(self):
        """Test sum outside tolerance fails."""
        validator = SumValidator(tolerance=0.01)
        data = {
            "items": [{"amount": 10.00}],
            "total": 10.50  # Outside 0.01 tolerance
        }
        result = validator.validate(data)
        assert result.valid is False
    
    def test_custom_field_names(self):
        """Test custom field names."""
        validator = SumValidator(
            items_field="line_items",
            amount_field="price",
            total_field="grand_total"
        )
        data = {
            "line_items": [
                {"price": 50.00},
                {"price": 50.00},
            ],
            "grand_total": 100.00
        }
        result = validator.validate(data)
        assert result.valid is True
    
    def test_missing_items_skipped(self):
        """Test missing items field is skipped."""
        validator = SumValidator()
        data = {"total": 100.00}
        result = validator.validate(data)
        assert result.valid is True
    
    def test_missing_total_skipped(self):
        """Test missing total field is skipped."""
        validator = SumValidator()
        data = {"items": [{"amount": 10.00}]}
        result = validator.validate(data)
        assert result.valid is True
    
    def test_empty_items_skipped(self):
        """Test empty items list is skipped."""
        validator = SumValidator()
        data = {"items": [], "total": 0}
        result = validator.validate(data)
        assert result.valid is True
    
    def test_invalid_total_type(self):
        """Test non-numeric total fails."""
        validator = SumValidator()
        data = {
            "items": [{"amount": 10.00}],
            "total": "not-a-number"
        }
        result = validator.validate(data)
        assert result.valid is False
        assert "not a number" in result.issues[0]
    
    def test_non_dict_items_skipped(self):
        """Test non-dict items in list are skipped."""
        validator = SumValidator()
        data = {
            "items": [{"amount": 10.00}, "invalid", None],
            "total": 10.00
        }
        result = validator.validate(data)
        assert result.valid is True
    
    def test_missing_amount_in_item(self):
        """Test missing amount field defaults to 0."""
        validator = SumValidator()
        data = {
            "items": [{"description": "no amount"}],
            "total": 0.00
        }
        result = validator.validate(data)
        assert result.valid is True


class TestSchemaValidator:
    """Tests for SchemaValidator."""
    
    def test_valid_object(self):
        """Test valid object matches schema."""
        schema = Object(properties={
            "name": String(),
            "age": Number(),
        })
        validator = SchemaValidator()
        data = {"name": "John", "age": 30}
        result = validator.validate(data, schema)
        assert result.valid is True
    
    def test_missing_field_allowed_by_default(self):
        """Test missing fields are allowed by default (lenient mode)."""
        # Our schema types have `required=[]` by default, which is falsy
        # So the validator treats missing fields as optional
        schema = Object(properties={
            "name": String(),
            "age": Number(),
        })
        validator = SchemaValidator()
        data = {"name": "John"}  # Missing age is allowed
        result = validator.validate(data, schema)
        # Missing fields are allowed by default in lenient mode
        assert result.valid is True
    
    def test_wrong_type_string(self):
        """Test wrong type for string fails."""
        schema = Object(properties={
            "name": String(),
        })
        validator = SchemaValidator()
        data = {"name": 123}  # Should be string
        result = validator.validate(data, schema)
        assert result.valid is False
        assert "expected string" in result.issues[0]
    
    def test_wrong_type_number(self):
        """Test wrong type for number fails."""
        schema = Object(properties={
            "age": Number(),
        })
        validator = SchemaValidator()
        data = {"age": "thirty"}  # Should be number
        result = validator.validate(data, schema)
        assert result.valid is False
        assert "expected number" in result.issues[0]
    
    def test_wrong_type_boolean(self):
        """Test wrong type for boolean fails."""
        schema = Object(properties={
            "active": Boolean(),
        })
        validator = SchemaValidator()
        data = {"active": "yes"}  # Should be boolean
        result = validator.validate(data, schema)
        assert result.valid is False
        assert "expected boolean" in result.issues[0]
    
    def test_valid_array(self):
        """Test valid array matches schema."""
        schema = Object(properties={
            "items": Array(items=String()),
        })
        validator = SchemaValidator()
        data = {"items": ["a", "b", "c"]}
        result = validator.validate(data, schema)
        assert result.valid is True
    
    def test_wrong_type_array(self):
        """Test wrong type for array fails."""
        schema = Object(properties={
            "items": Array(items=String()),
        })
        validator = SchemaValidator()
        data = {"items": "not-an-array"}
        result = validator.validate(data, schema)
        assert result.valid is False
        assert "expected array" in result.issues[0]
    
    def test_array_item_wrong_type(self):
        """Test array item with wrong type fails."""
        schema = Object(properties={
            "items": Array(items=Number()),
        })
        validator = SchemaValidator()
        data = {"items": [1, 2, "three"]}  # Third item wrong type
        result = validator.validate(data, schema)
        assert result.valid is False
        assert "[2]" in result.issues[0]  # Index 2 is wrong
    
    def test_nested_object(self):
        """Test nested object validation."""
        schema = Object(properties={
            "address": Object(properties={
                "city": String(),
                "zip": String(),
            })
        })
        validator = SchemaValidator()
        data = {"address": {"city": "NYC", "zip": "10001"}}
        result = validator.validate(data, schema)
        assert result.valid is True
    
    def test_nested_object_wrong_type(self):
        """Test nested object with wrong type fails."""
        schema = Object(properties={
            "address": Object(properties={
                "city": String(),
            })
        })
        validator = SchemaValidator()
        data = {"address": "123 Main St"}  # Should be object
        result = validator.validate(data, schema)
        assert result.valid is False
        assert "expected object" in result.issues[0]
    
    def test_strict_mode_extra_fields(self):
        """Test strict mode rejects extra fields."""
        schema = Object(properties={
            "name": String(),
        })
        validator = SchemaValidator(strict=True)
        data = {"name": "John", "extra": "field"}
        result = validator.validate(data, schema)
        assert result.valid is False
        assert "unexpected field" in result.issues[0]
    
    def test_non_strict_mode_extra_fields(self):
        """Test non-strict mode allows extra fields."""
        schema = Object(properties={
            "name": String(),
        })
        validator = SchemaValidator(strict=False)
        data = {"name": "John", "extra": "field"}
        result = validator.validate(data, schema)
        assert result.valid is True
    
    def test_no_schema_passes(self):
        """Test validation with no schema always passes."""
        validator = SchemaValidator()
        data = {"anything": "goes"}
        result = validator.validate(data, schema=None)
        assert result.valid is True
    
    def test_int_as_number(self):
        """Test int is accepted as number."""
        schema = Object(properties={
            "count": Number(),
        })
        validator = SchemaValidator()
        data = {"count": 42}  # int, not float
        result = validator.validate(data, schema)
        assert result.valid is True
    
    def test_float_as_number(self):
        """Test float is accepted as number."""
        schema = Object(properties={
            "price": Number(),
        })
        validator = SchemaValidator()
        data = {"price": 19.99}
        result = validator.validate(data, schema)
        assert result.valid is True
