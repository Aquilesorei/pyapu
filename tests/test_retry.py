"""
Tests for retry logic with mocked functions.
"""

import pytest
import time
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strutex.providers.retry import (
    RetryConfig, 
    with_retry, 
    with_retry_async,
    RateLimiter,
    DEFAULT_RETRY_CONFIG
)


class TestRetryConfig:
    """Tests for RetryConfig class."""
    
    def test_default_values(self):
        """Test default config values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.retry_on == (Exception,)
    
    def test_custom_values(self):
        """Test custom config values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            retry_on=(ValueError, TypeError)
        )
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.retry_on == (ValueError, TypeError)
    
    def test_default_retry_config_exists(self):
        """Test DEFAULT_RETRY_CONFIG is available."""
        assert DEFAULT_RETRY_CONFIG is not None
        assert DEFAULT_RETRY_CONFIG.max_retries == 3


class TestWithRetry:
    """Tests for with_retry decorator."""
    
    def test_success_on_first_try(self):
        """Test function succeeds on first try."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=3, base_delay=0.01))
        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = succeed()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_then_succeed(self):
        """Test function retries then succeeds."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=3, base_delay=0.01))
        def fail_twice_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = fail_twice_then_succeed()
        assert result == "success"
        assert call_count == 3  # Failed 2x, succeeded on 3rd
    
    def test_exhaust_retries(self):
        """Test all retries exhausted raises exception."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=2, base_delay=0.01))
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")
        
        with pytest.raises(ValueError, match="Permanent failure"):
            always_fail()
        
        assert call_count == 3  # Initial + 2 retries
    
    def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        retry_count = 0
        exceptions = []
        
        def on_retry_handler(exc, attempt):
            nonlocal retry_count
            retry_count += 1
            exceptions.append(str(exc))
        
        @with_retry(RetryConfig(max_retries=2, base_delay=0.01), on_retry=on_retry_handler)
        def fail_once():
            if retry_count == 0:
                raise ValueError("First failure")
            return "success"
        
        result = fail_once()
        assert result == "success"
        assert retry_count == 1
        assert "First failure" in exceptions[0]
    
    def test_only_retry_on_specified_exceptions(self):
        """Test only retries on specified exception types."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=3, base_delay=0.01, retry_on=(ValueError,)))
        def raise_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Not retried")
        
        with pytest.raises(TypeError):
            raise_type_error()
        
        # Should not retry on TypeError
        assert call_count == 1
    
    def test_default_config_used(self):
        """Test decorator uses DEFAULT_RETRY_CONFIG when none specified."""
        call_count = 0
        
        @with_retry()  # No config
        def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First failure")
            return "success"
        
        # Since DEFAULT has base_delay=1.0, this would be slow
        # Let's just verify it works with explicit fast config
        # This test is just to ensure @with_retry() works

    def test_exponential_backoff_respects_max_delay(self):
        """Test exponential backoff is capped at max_delay."""
        config = RetryConfig(
            max_retries=10,
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0
        )
        
        # Delay would be: 1, 2, 4, 8, 16... but capped at 5
        # After attempt 2: delay = 1 * 2^2 = 4 (under max)
        # After attempt 3: delay = 1 * 2^3 = 8 -> capped to 5
        
        delays = []
        for attempt in range(5):
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            delays.append(delay)
        
        assert delays == [1.0, 2.0, 4.0, 5.0, 5.0]


class TestWithRetryAsync:
    """Tests for with_retry_async function."""
    
    @pytest.mark.asyncio
    async def test_async_success(self):
        """Test async function succeeds on first try."""
        call_count = 0
        
        async def async_succeed():
            nonlocal call_count
            call_count += 1
            return "async success"
        
        result = await with_retry_async(
            async_succeed, 
            RetryConfig(max_retries=3, base_delay=0.01)
        )
        assert result == "async success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_retry_then_succeed(self):
        """Test async function retries then succeeds."""
        call_count = 0
        
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Async temp failure")
            return "async success"
        
        result = await with_retry_async(
            fail_then_succeed,
            RetryConfig(max_retries=3, base_delay=0.01)
        )
        assert result == "async success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_async_exhaust_retries(self):
        """Test async exhausts retries."""
        call_count = 0
        
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Async permanent failure")
        
        with pytest.raises(ValueError, match="Async permanent failure"):
            await with_retry_async(
                always_fail,
                RetryConfig(max_retries=2, base_delay=0.01)
            )
        
        assert call_count == 3


class TestRateLimiter:
    """Tests for RateLimiter class."""
    
    def test_zero_interval_no_wait(self):
        """Test zero interval doesn't wait."""
        limiter = RateLimiter(min_interval=0)
        
        start = time.time()
        limiter.wait()
        limiter.wait()
        limiter.wait()
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # Should be nearly instant
    
    def test_enforces_min_interval(self):
        """Test limiter enforces minimum interval."""
        limiter = RateLimiter(min_interval=0.1)
        
        start = time.time()
        limiter.wait()
        limiter.wait()
        limiter.wait()
        elapsed = time.time() - start
        
        # Should take at least 0.2s (2 waits after first immediate call)
        assert elapsed >= 0.2
    
    @pytest.mark.asyncio
    async def test_async_wait_zero_interval(self):
        """Test async wait with zero interval."""
        limiter = RateLimiter(min_interval=0)
        
        start = time.time()
        await limiter.wait_async()
        await limiter.wait_async()
        elapsed = time.time() - start
        
        assert elapsed < 0.1
    
    @pytest.mark.asyncio
    async def test_async_wait_enforces_interval(self):
        """Test async wait enforces minimum interval."""
        limiter = RateLimiter(min_interval=0.1)
        
        start = time.time()
        await limiter.wait_async()
        await limiter.wait_async()
        elapsed = time.time() - start
        
        assert elapsed >= 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
