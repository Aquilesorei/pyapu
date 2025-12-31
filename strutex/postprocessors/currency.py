"""
Currency normalizer postprocessor - converts amounts to base currency.
"""

import logging
from typing import Any, Dict, List, Optional

from ..plugins.base import Postprocessor

logger = logging.getLogger("strutex.postprocessors.currency")


class CurrencyNormalizer(Postprocessor, name="currency"):
    """
    Convert monetary amounts to a base currency.
    
    Adds normalized fields with `_base` suffix containing converted amounts.
    Optionally fetches live exchange rates from a free API.
    
    Attributes:
        base_currency: Target currency code (e.g., "USD", "EUR")
        amount_fields: Fields containing monetary amounts
        currency_field: Field containing the source currency code
        exchange_rates: Static exchange rates dict
        
    Example:
        >>> normalizer = CurrencyNormalizer(
        ...     base_currency="USD",
        ...     exchange_rates={"EUR": 1.10, "GBP": 1.27}
        ... )
        >>> normalizer.process({"total": 100, "currency": "EUR"})
        {"total": 100, "currency": "EUR", "total_usd": 110.0}
    """
    
    priority = 45
    
    # Free exchange rate API (no key required for limited use)
    EXCHANGE_API = "https://api.exchangerate-api.com/v4/latest/{base}"
    
    # Common default rates (fallback if API unavailable)
    DEFAULT_RATES = {
        "USD": 1.0,
        "EUR": 1.08,
        "GBP": 1.27,
        "JPY": 0.0067,
        "CHF": 1.13,
        "CAD": 0.74,
        "AUD": 0.65,
        "CNY": 0.14,
        "INR": 0.012,
    }
    
    def __init__(
        self,
        base_currency: str = "USD",
        amount_fields: Optional[List[str]] = None,
        currency_field: str = "currency",
        exchange_rates: Optional[Dict[str, float]] = None,
        fetch_rates: bool = False,
        rates_cache_seconds: int = 3600
    ):
        """
        Initialize the currency normalizer.
        
        Args:
            base_currency: Target currency to convert to (e.g., "USD", "EUR").
            amount_fields: Fields to convert. Defaults to ["total", "subtotal", "amount"].
            currency_field: Field containing source currency code.
            exchange_rates: Static rates dict mapping currency code to rate vs base.
                Rate means: 1 unit of foreign currency = rate units of base currency.
            fetch_rates: If True, fetch live rates from API on first use.
            rates_cache_seconds: How long to cache fetched rates.
        """
        self.base_currency = base_currency.upper()
        self.amount_fields = amount_fields or ["total", "subtotal", "amount", "tax", "grand_total"]
        self.currency_field = currency_field
        self.fetch_rates = fetch_rates
        self.rates_cache_seconds = rates_cache_seconds
        
        # Initialize rates
        if exchange_rates:
            self._rates = {k.upper(): v for k, v in exchange_rates.items()}
        else:
            self._rates = self.DEFAULT_RATES.copy()
        
        self._rates_cached_at: Optional[float] = None
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert amount fields to base currency.
        
        Args:
            data: Extracted data dictionary
            
        Returns:
            Data with added `_<base>` suffix fields for converted amounts
        """
        result = data.copy()
        
        # Get source currency
        source_currency = data.get(self.currency_field, "").upper()
        if not source_currency:
            # No currency specified, assume already in base currency
            return result
        
        if source_currency == self.base_currency:
            # Already in base currency, no conversion needed
            return result
        
        # Fetch rates if needed
        if self.fetch_rates:
            self._maybe_fetch_rates()
        
        # Get conversion rate
        rate = self._get_rate(source_currency)
        if rate is None:
            logger.warning(f"No exchange rate for {source_currency} to {self.base_currency}")
            return result
        
        # Convert each amount field
        suffix = f"_{self.base_currency.lower()}"
        for field in self.amount_fields:
            if field not in data:
                continue
            
            value = data[field]
            if value is None:
                continue
            
            try:
                amount = float(value)
                converted = round(amount * rate, 2)
                result[f"{field}{suffix}"] = converted
            except (TypeError, ValueError):
                continue
        
        return result
    
    def _get_rate(self, source_currency: str) -> Optional[float]:
        """
        Get exchange rate from source to base currency.
        
        Rate = how many base currency units for 1 source currency unit.
        """
        source_currency = source_currency.upper()
        
        if source_currency == self.base_currency:
            return 1.0
        
        # Check if we have rate for source currency
        if source_currency in self._rates:
            source_rate = self._rates[source_currency]
            base_rate = self._rates.get(self.base_currency, 1.0)
            # Convert: source -> USD -> base
            return source_rate / base_rate if base_rate != 0 else None
        
        return None
    
    def _maybe_fetch_rates(self) -> None:
        """Fetch rates from API if cache is stale."""
        import time
        
        now = time.time()
        if self._rates_cached_at and (now - self._rates_cached_at) < self.rates_cache_seconds:
            return
        
        try:
            self._fetch_rates_from_api()
            self._rates_cached_at = now
        except Exception as e:
            logger.warning(f"Failed to fetch exchange rates: {e}")
    
    def _fetch_rates_from_api(self) -> None:
        """Fetch current exchange rates from API."""
        import urllib.request
        import json
        
        url = self.EXCHANGE_API.format(base="USD")
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                
            rates = data.get("rates", {})
            if rates:
                # API returns rates where USD = 1, so invert for our format
                self._rates = {}
                for currency, rate in rates.items():
                    if rate > 0:
                        self._rates[currency.upper()] = 1.0 / rate
                
                logger.debug(f"Fetched {len(self._rates)} exchange rates")
                
        except Exception as e:
            raise RuntimeError(f"Exchange rate API error: {e}")
    
    def set_rate(self, currency: str, rate: float) -> None:
        """
        Manually set an exchange rate.
        
        Args:
            currency: Currency code (e.g., "EUR")
            rate: Rate vs USD (e.g., 1.10 means 1 EUR = 1.10 USD)
        """
        self._rates[currency.upper()] = rate
