"""
Postprocessor chain - compose multiple postprocessors.
"""

from typing import Any, Dict, List

from ..plugins.base import Postprocessor


class PostprocessorChain(Postprocessor, name="chain", register=False):
    """
    Chain multiple postprocessors together.
    
    Runs each postprocessor in sequence, passing the output of one
    to the input of the next.
    
    Example:
        >>> chain = PostprocessorChain([
        ...     DatePostprocessor(),
        ...     NumberPostprocessor(),
        ...     CurrencyNormalizer(base_currency="USD"),
        ... ])
        >>> chain.process(data)
    """
    
    def __init__(self, postprocessors: List[Postprocessor]):
        """
        Initialize the postprocessor chain.
        
        Args:
            postprocessors: List of postprocessors to run in order.
        """
        self.postprocessors = postprocessors
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all postprocessors in sequence.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Transformed data after all postprocessors
        """
        result = data
        for pp in self.postprocessors:
            result = pp.process(result)
        return result
    
    def add(self, postprocessor: Postprocessor) -> "PostprocessorChain":
        """Add a postprocessor to the chain. Returns self for chaining."""
        self.postprocessors.append(postprocessor)
        return self
    
    def __len__(self) -> int:
        return len(self.postprocessors)
    
    def __iter__(self):
        return iter(self.postprocessors)
