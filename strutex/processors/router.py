"""
Router processor - routes documents to specialized processors based on content.
"""

import logging
from typing import Any, Dict, Optional, Union, Callable

from .base import Processor
from .simple import SimpleProcessor

logger = logging.getLogger("strutex.processors.router")

class RouterProcessor(Processor):
    """
    Processor that routes documents based on classification.
    
    Example:
        >>> router = RouterProcessor(
        ...     routes={
        ...         "invoice": invoice_processor,
        ...         "resume": resume_processor
        ...     },
        ...     classifier=my_classifier_fn
        ... )
    """
    
    def __init__(
        self,
        routes: Dict[str, Processor],
        classifier: Optional[Union[Callable[[str], str], Processor]] = None,
        default_route: Optional[str] = None,
        **kwargs
    ):
        """
        Args:
            routes: Mapping of labels to Processor instances.
            classifier: A function that takes file content and returns a label,
                       or a Processor that extracts a label.
            default_route: Label to use if classification fails or is unknown.
            **kwargs: Shared configuration.
        """
        super().__init__(**kwargs)
        self._routes = routes
        self._classifier = classifier
        self._default_route = default_route
        
    def _classify(self, content: str) -> str:
        """Determine the document type."""
        if self._classifier is None:
            return self._default_route or ""
            
        if callable(self._classifier):
            try:
                return self._classifier(content)
            except Exception as e:
                logger.warning(f"Classifier function failed: {e}")
                return self._default_route or ""
        
        # If classifier is a processor, we assume it's set up to return a label
        # This is a bit recursive, so we'd need a simple extraction prompt here.
        # For now, let's keep it simple with callable or hardcoded logic.
        return self._default_route or ""

    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Any] = None,
        model: Optional[Any] = None,
        **kwargs
    ) -> Any:
        # 1. Load content to classify
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000) # Read first 2k chars for classification
            
        # 2. Classify
        label = self._classify(content)
        logger.info(f"Routed document to: {label or 'default'}")
        
        # 3. Get processor
        processor = self._routes.get(label)
        if not processor:
            if self._default_route and self._default_route in self._routes:
                processor = self._routes[self._default_route]
            else:
                # Fallback to a simple processor if no route matches
                processor = SimpleProcessor(**self._config)
                
        # 4. Delegate
        return processor.process(file_path, prompt, schema=schema, model=model, **kwargs)

    async def aprocess(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Any] = None,
        model: Optional[Any] = None,
        **kwargs
    ) -> Any:
        # Same logic but async
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000)
            
        label = self._classify(content)
        processor = self._routes.get(label)
        
        if not processor:
            if self._default_route and self._default_route in self._routes:
                processor = self._routes[self._default_route]
            else:
                processor = SimpleProcessor(**self._config)
                
        return await processor.aprocess(file_path, prompt, schema=schema, model=model, **kwargs)
