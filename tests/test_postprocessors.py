"""
Tests for postprocessor plugins.
"""

import pytest
from strutex.postprocessors import (
    DatePostprocessor,
    NumberPostprocessor,
    CurrencyNormalizer,
    PostprocessorChain,
)


class TestDatePostprocessor:
    """Tests for DatePostprocessor."""
    
    def test_dynamic_formats(self):
        """Should support formats generated dynamically from separators."""
        # Test with space separator
        pp = DatePostprocessor(separators=[" "])
        result = pp.process({"date": "15 01 2024"})
        assert result["date"] == "2024-01-15"
        
        # Test with mixed/custom separator
        pp = DatePostprocessor(separators=["_"])
        result = pp.process({"date": "2024_01_15"})
        assert result["date"] == "2024-01-15"

    def test_year_range_validation(self):
        """Should reject dates outside min/max year range."""
        pp = DatePostprocessor(min_year=2000, max_year=2025)
        
        # Valid date
        assert pp.process({"date": "15.01.2024"})["date"] == "2024-01-15"
        
        # Too old
        assert pp.process({"date": "15.01.1999"})["date"] == "15.01.1999"  # Unchanged
        
        # Too future
        assert pp.process({"date": "15.01.2030"})["date"] == "15.01.2030"  # Unchanged

    def test_text_month_formats(self):
        """Should handle text month formats."""
        pp = DatePostprocessor()
        
        # Long month
        res = pp.process({"date": "January 15, 2024"})
        assert res["date"] == "2024-01-15"
        
        # Short month
        res = pp.process({"date": "15 Jan 2024"})
        assert res["date"] == "2024-01-15"

    def test_no_separator_formats(self):
        """Should handle formats without separators (e.g. YYYYMMDD)."""
        pp = DatePostprocessor()
        
        # YYYYMMDD
        res = pp.process({"date": "20240115"})
        assert res["date"] == "2024-01-15"
        
        # DDMMYYYY
        res = pp.process({"date": "15012024"})
        assert res["date"] == "2024-01-15"
        
        # MMDDYYYY (US) - ambiguous with DDMMYYYY if day <= 12, but tries in order
        # Default order puts European checks before US often, or depends on generation list order.
        # Let's check a clear US date: 01/30/2024 -> 01302024
        res = pp.process({"date": "12312024"}) # Dec 31
        assert res["date"] == "2024-12-31"

    
    def test_auto_detect_date_fields(self):
        """Fields with 'date' in name should be auto-detected."""
        pp = DatePostprocessor()
        result = pp.process({
            "invoice_date": "15.01.2024",
            "name": "John",
            "amount": 100
        })
        assert result["invoice_date"] == "2024-01-15"
        assert result["name"] == "John"
        assert result["amount"] == 100
    
    def test_specific_fields_only(self):
        """When date_fields specified, only process those."""
        pp = DatePostprocessor(date_fields=["custom"])
        result = pp.process({
            "invoice_date": "15.01.2024",
            "custom": "20.02.2024"
        })
        assert result["invoice_date"] == "15.01.2024"  # Not processed
        assert result["custom"] == "2024-02-20"  # Processed
    
    def test_none_values_unchanged(self):
        """None values should remain None."""
        pp = DatePostprocessor()
        result = pp.process({"invoice_date": None})
        assert result["invoice_date"] is None
    
    def test_empty_string_unchanged(self):
        """Empty strings should remain empty."""
        pp = DatePostprocessor()
        result = pp.process({"invoice_date": ""})
        assert result["invoice_date"] == ""


class TestNumberPostprocessor:
    """Tests for NumberPostprocessor."""
    
    def test_us_currency_format(self):
        """$1,234.56 should parse to 1234.56."""
        pp = NumberPostprocessor()
        result = pp.process({"total": "$1,234.56"})
        assert result["total"] == 1234.56
    
    def test_european_format(self):
        """1.234,56 should parse correctly with de_DE locale."""
        pp = NumberPostprocessor(locale="de_DE")
        result = pp.process({"total": "1.234,56"})
        assert result["total"] == 1234.56
    
    def test_euro_symbol(self):
        """Euro symbol should be stripped."""
        pp = NumberPostprocessor()
        result = pp.process({"amount": "€500.00"})
        assert result["amount"] == 500.0
    
    def test_negative_parentheses(self):
        """(123.45) should parse as -123.45."""
        pp = NumberPostprocessor()
        result = pp.process({"total": "(123.45)"})
        assert result["total"] == -123.45
    
    def test_auto_detect_amount_fields(self):
        """Fields with 'amount', 'total', etc. should be auto-detected."""
        pp = NumberPostprocessor()
        result = pp.process({
            "total": "$100.00",
            "subtotal": "50.00",
            "name": "Test",
            "price": "$25.50"
        })
        assert result["total"] == 100.0
        assert result["subtotal"] == 50.0
        assert result["name"] == "Test"
        assert result["price"] == 25.5
    
    def test_already_numeric_unchanged(self):
        """Already numeric values should pass through."""
        pp = NumberPostprocessor()
        result = pp.process({"total": 100.5})
        assert result["total"] == 100.5
    
    def test_none_values_unchanged(self):
        """None values should remain None."""
        pp = NumberPostprocessor()
        result = pp.process({"total": None})
        assert result["total"] is None


class TestCurrencyNormalizer:
    """Tests for CurrencyNormalizer."""
    
    def test_eur_to_usd(self):
        """EUR to USD conversion with static rate."""
        pp = CurrencyNormalizer(
            base_currency="USD",
            exchange_rates={"EUR": 1.10}
        )
        result = pp.process({"total": 100, "currency": "EUR"})
        assert result["total"] == 100  # Original unchanged
        assert result["total_usd"] == 110.0  # Converted
    
    def test_same_currency_no_conversion(self):
        """Same currency should not add converted fields."""
        pp = CurrencyNormalizer(base_currency="USD")
        result = pp.process({"total": 100, "currency": "USD"})
        assert result["total"] == 100
        assert "total_usd" not in result
    
    def test_missing_currency_field(self):
        """Missing currency field should not convert."""
        pp = CurrencyNormalizer(base_currency="USD")
        result = pp.process({"total": 100})
        assert result["total"] == 100
        assert "total_usd" not in result
    
    def test_multiple_amount_fields(self):
        """Multiple amount fields should all be converted."""
        pp = CurrencyNormalizer(
            base_currency="USD",
            exchange_rates={"GBP": 1.27}
        )
        result = pp.process({
            "total": 100,
            "subtotal": 80,
            "currency": "GBP"
        })
        assert result["total_usd"] == 127.0
        assert result["subtotal_usd"] == 101.6
    
    def test_set_rate_manually(self):
        """Manual rate setting should work."""
        pp = CurrencyNormalizer(base_currency="EUR")
        pp.set_rate("JPY", 0.0062)
        result = pp.process({"total": 10000, "currency": "JPY"})
        assert "total_eur" in result


class TestPostprocessorChain:
    """Tests for PostprocessorChain."""
    
    def test_chain_execution_order(self):
        """Postprocessors should run in order."""
        chain = PostprocessorChain([
            DatePostprocessor(),
            NumberPostprocessor(),
        ])
        result = chain.process({
            "invoice_date": "15.01.2024",
            "total": "$1,000.00"
        })
        assert result["invoice_date"] == "2024-01-15"
        assert result["total"] == 1000.0
    
    def test_chain_len(self):
        """Chain should report correct length."""
        chain = PostprocessorChain([
            DatePostprocessor(),
            NumberPostprocessor(),
        ])
        assert len(chain) == 2
    
    def test_chain_add(self):
        """Adding postprocessors should work."""
        chain = PostprocessorChain([DatePostprocessor()])
        chain.add(NumberPostprocessor())
        assert len(chain) == 2
    
    def test_chain_iteration(self):
        """Chain should be iterable."""
        chain = PostprocessorChain([
            DatePostprocessor(),
            NumberPostprocessor(),
        ])
        items = list(chain)
        assert len(items) == 2
        assert isinstance(items[0], DatePostprocessor)
        assert isinstance(items[1], NumberPostprocessor)
