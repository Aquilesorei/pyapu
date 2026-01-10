"""
Processing context for stateful, multi-step document workflows.

Provides shared state, history tracking, and workflow coordination
across multiple extraction steps.
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger("strutex.context")


@dataclass
class ExtractionStep:
    """Record of a single extraction step."""
    step_id: str
    file_path: str
    prompt: str
    provider: str
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProcessingContext:
    """
    Context for multi-step document processing workflows.
    
    Maintains state, history, and coordination across multiple
    extraction steps. Useful for:
    - Multi-page document processing
    - Chained extractions (extract -> validate -> enrich)
    - Aggregating results from multiple documents
    - Tracking extraction history and metrics
    
    Example:
        >>> ctx = ProcessingContext()
        >>> 
        >>> # First extraction
        >>> invoice = ctx.extract(processor, "invoice.pdf", "Extract", INVOICE_US)
        >>> 
        >>> # Use results in next step
        >>> ctx.set("invoice_total", invoice.total)
        >>> 
        >>> # Second extraction with context
        >>> receipt = ctx.extract(
        ...     processor, "receipt.jpg", 
        ...     f"Verify total matches {ctx.get('invoice_total')}", 
        ...     RECEIPT
        ... )
        >>> 
        >>> # Check history
        >>> print(f"Processed {len(ctx.history)} documents")
        >>> print(f"Total time: {ctx.total_duration_ms}ms")
    """
    
    def __init__(
        self,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            context_id: Unique context identifier (auto-generated if not provided)
            metadata: Initial metadata for the context
        """
        self.context_id = context_id or str(uuid.uuid4())[:8]
        self.metadata = metadata or {}
        self._state: Dict[str, Any] = {}
        self._history: List[ExtractionStep] = []
        self._listeners: List[Callable[[ExtractionStep], None]] = []
        self._created_at = datetime.utcnow()
        
        logger.debug(f"Created ProcessingContext {self.context_id}")
    
    # === State Management ===
    
    def set(self, key: str, value: Any) -> None:
        """Store a value in the context state."""
        self._state[key] = value
        logger.debug(f"Context {self.context_id}: set {key}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the context state."""
        return self._state.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if a key exists in context state."""
        return key in self._state
    
    def update(self, data: Dict[str, Any]) -> None:
        """Update context state with multiple values."""
        self._state.update(data)
    
    def clear_state(self) -> None:
        """Clear all state (but preserve history)."""
        self._state.clear()
    
    @property
    def state(self) -> Dict[str, Any]:
        """Read-only access to current state."""
        return self._state.copy()
    
    # === Extraction ===
    
    def extract(
        self,
        processor,  # DocumentProcessor
        file_path: str,
        prompt: str,
        schema: Any,
        **kwargs
    ) -> Any:
        """
        Perform an extraction step within this context.
        
        Automatically tracks history, timing, and state.
        
        Args:
            processor: DocumentProcessor instance
            file_path: Path to document
            prompt: Extraction prompt
            schema: Output schema or Pydantic model
            **kwargs: Additional processor arguments
            
        Returns:
            Extraction result
            
        Raises:
            Exception: If extraction fails
        """
        step_id = f"{self.context_id}-{len(self._history) + 1}"
        start_time = time.time()
        
        # Get provider name
        provider_name = "unknown"
        if hasattr(processor, '_provider'):
            provider_name = processor._provider.__class__.__name__
        elif hasattr(processor, 'provider'):
            p = processor.provider
            provider_name = p.__class__.__name__ if p else "unknown"
        
        step = ExtractionStep(
            step_id=step_id,
            file_path=file_path,
            prompt=prompt[:200],  # Truncate for storage
            provider=provider_name,
            metadata=kwargs.get("metadata", {})
        )
        
        try:
            # Try Pydantic model first, then fall back to schema
            if hasattr(schema, 'model_fields'):  # Pydantic model
                result = processor.process(
                    file_path=file_path,
                    prompt=prompt,
                    model=schema,
                    **kwargs
                )
            else:
                result = processor.process(
                    file_path=file_path,
                    prompt=prompt,
                    schema=schema,
                    **kwargs
                )
            
            # Extract usage metadata if present
            if isinstance(result, dict) and "_usage" in result:
                step.metadata["usage"] = result["_usage"]
                # We optionally keep or remove it. For now, let's keep it but 
                # also promote it to metadata for aggregation.
            
            step.result = result
            step.duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"Context {self.context_id}: Step {step_id} completed "
                f"in {step.duration_ms:.0f}ms"
            )
            
            return result
            
        except Exception as e:
            step.error = str(e)
            step.duration_ms = (time.time() - start_time) * 1000
            
            logger.error(f"Context {self.context_id}: Step {step_id} failed: {e}")
            raise
            
        finally:
            self._history.append(step)
            self._notify_listeners(step)
    
    async def aextract(
        self,
        processor,
        file_path: str,
        prompt: str,
        schema: Any,
        **kwargs
    ) -> Any:
        """Async version of extract."""
        step_id = f"{self.context_id}-{len(self._history) + 1}"
        start_time = time.time()
        
        provider_name = "unknown"
        if hasattr(processor, '_provider'):
            provider_name = processor._provider.__class__.__name__
        
        step = ExtractionStep(
            step_id=step_id,
            file_path=file_path,
            prompt=prompt[:200],
            provider=provider_name,
            metadata=kwargs.get("metadata", {})
        )
        
        try:
            if hasattr(schema, 'model_fields'):
                result = await processor.aprocess(
                    file_path=file_path,
                    prompt=prompt,
                    model=schema,
                    **kwargs
                )
            else:
                result = await processor.aprocess(
                    file_path=file_path,
                    prompt=prompt,
                    schema=schema,
                    **kwargs
                )
            
            # Extract usage metadata if present
            if isinstance(result, dict) and "_usage" in result:
                step.metadata["usage"] = result["_usage"]
            
            step.result = result
            step.duration_ms = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            step.error = str(e)
            step.duration_ms = (time.time() - start_time) * 1000
            raise
            
        finally:
            self._history.append(step)
            self._notify_listeners(step)
    
    # === History & Metrics ===
    
    @property
    def history(self) -> List[ExtractionStep]:
        """Get extraction history (read-only copy)."""
        return self._history.copy()
    
    @property
    def last_result(self) -> Optional[Any]:
        """Get the result from the last successful extraction."""
        for step in reversed(self._history):
            if step.result is not None:
                return step.result
        return None
    
    @property
    def last_error(self) -> Optional[str]:
        """Get the error from the last failed extraction."""
        for step in reversed(self._history):
            if step.error is not None:
                return step.error
        return None
    
    @property
    def total_duration_ms(self) -> float:
        """Total processing time across all steps."""
        return sum(s.duration_ms for s in self._history)
    
    @property
    def success_count(self) -> int:
        """Number of successful extractions."""
        return sum(1 for s in self._history if s.result is not None)
    
    @property
    def error_count(self) -> int:
        """Number of failed extractions."""
        return sum(1 for s in self._history if s.error is not None)
    
    def get_results(self) -> List[Any]:
        """Get all successful results."""
        return [s.result for s in self._history if s.result is not None]
        
    @property
    def total_tokens(self) -> int:
        """Total tokens used across all steps."""
        return sum(s.metadata.get("usage", {}).get("total_tokens", 0) for s in self._history)

    @property
    def total_cost(self) -> float:
        """Total estimated cost across all steps."""
        return sum(s.metadata.get("usage", {}).get("total_cost", 0.0) for s in self._history)
    
    # === Listeners ===
    
    def on_step(self, callback: Callable[[ExtractionStep], None]) -> None:
        """
        Register a callback for each extraction step.
        
        Called after each extraction (success or failure).
        
        Args:
            callback: Function that receives ExtractionStep
        """
        self._listeners.append(callback)
    
    def _notify_listeners(self, step: ExtractionStep) -> None:
        """Notify all listeners of a completed step."""
        for listener in self._listeners:
            try:
                listener(step)
            except Exception as e:
                logger.warning(f"Listener error: {e}")
    
    # === Serialization ===
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary."""
        return {
            "context_id": self.context_id,
            "metadata": self.metadata,
            "state": self._state,
            "history": [
                {
                    "step_id": s.step_id,
                    "file_path": s.file_path,
                    "prompt": s.prompt,
                    "provider": s.provider,
                    "result": s.result,
                    "error": s.error,
                    "duration_ms": s.duration_ms,
                    "timestamp": s.timestamp,
                }
                for s in self._history
            ],
            "created_at": self._created_at.isoformat(),
            "total_duration_ms": self.total_duration_ms,
            "success_count": self.success_count,
            "error_count": self.error_count,
        }
    
    def __repr__(self) -> str:
        return (
            f"ProcessingContext(id={self.context_id}, "
            f"steps={len(self._history)}, "
            f"state_keys={list(self._state.keys())})"
        )


class BatchContext(ProcessingContext):
    """
    Context optimized for batch processing multiple documents.
    
    Adds batch-specific features like progress tracking and
    aggregate statistics.
    
    Example:
        >>> ctx = BatchContext(total_documents=10)
        >>> 
        >>> for pdf in pdf_files:
        ...     result = ctx.extract(processor, pdf, "Extract", INVOICE_US)
        ...     print(f"Progress: {ctx.progress_percent}%")
        >>> 
        >>> print(f"Success rate: {ctx.success_rate}%")
    """
    
    def __init__(
        self,
        total_documents: int,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(context_id, metadata)
        self.total_documents = total_documents
        
    def add_result(self, file_path: str, result: Any, metadata: Optional[Dict[str, Any]] = None, duration_ms: float = 0.0) -> None:
        """Manually add a successful result to history.
        
        Args:
            file_path: Path to the processed document
            result: Extraction result
            metadata: Optional metadata dict
            duration_ms: Processing duration in milliseconds (default: 0.0)
        """
        step_id = f"{self.context_id}-{len(self._history) + 1}"
        step = ExtractionStep(
            step_id=step_id,
            file_path=file_path,
            prompt="Batch Process",
            provider="unknown",
            result=result,
            metadata=metadata or {},
            duration_ms=duration_ms
        )
        self._history.append(step)
        self._notify_listeners(step)
        
    def add_error(self, file_path: str, error: Exception, metadata: Optional[Dict[str, Any]] = None, duration_ms: float = 0.0) -> None:
        """Manually add a failure to history.
        
        Args:
            file_path: Path to the failed document
            error: The exception that occurred
            metadata: Optional metadata dict
            duration_ms: Processing duration in milliseconds (default: 0.0)
        """
        step_id = f"{self.context_id}-{len(self._history) + 1}"
        step = ExtractionStep(
            step_id=step_id,
            file_path=file_path,
            prompt="Batch Process",
            provider="unknown",
            error=str(error),
            metadata=metadata or {},
            duration_ms=duration_ms
        )
        self._history.append(step)
        self._notify_listeners(step)
    
    @property
    def results(self) -> Dict[str, Any]:
        """Dictionary mapping file paths to their extraction results."""
        return {s.file_path: s.result for s in self._history if s.result is not None}

    @property
    def progress(self) -> int:
        """Number of documents processed."""
        return len(self._history)
    
    @property
    def progress_percent(self) -> float:
        """Processing progress as percentage."""
        if self.total_documents == 0:
            return 100.0
        return (self.progress / self.total_documents) * 100
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.progress == 0:
            return 0.0
        return (self.success_count / self.progress) * 100
    
    @property
    def average_duration_ms(self) -> float:
        """Average extraction time per document."""
        if self.progress == 0:
            return 0.0
        return self.total_duration_ms / self.progress
    
    @property
    def estimated_remaining_ms(self) -> float:
        """Estimated time remaining based on average."""
        remaining = self.total_documents - self.progress
        return remaining * self.average_duration_ms
