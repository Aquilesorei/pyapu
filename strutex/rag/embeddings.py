"""
Embedding services for strutex RAG.
Provides local embedding generation using FastEmbed.
"""
from typing import List, Optional, Union
import numpy as np

try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False


class EmbeddingService:
    """Base class for embedding services."""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        raise NotImplementedError

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        raise NotImplementedError


class FastEmbedService(EmbeddingService):
    """
    Local embedding service using FastEmbed.
    
    FastEmbed is a lightweight and fast library for text embeddings.
    It runs locally and doesn't require an API key.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        cache_dir: Optional[str] = None,
        threads: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize the FastEmbed service.
        
        Args:
            model_name: The model to use for embeddings.
            cache_dir: Optional directory to cache models.
            threads: Number of threads to use for inference.
        """
        if not FASTEMBED_AVAILABLE:
            raise ImportError(
                "fastembed is not installed. Please install it with: "
                "pip install 'strutex[rag]'"
            )
        
        self.model_name = model_name
        self.embedding_model = TextEmbedding(
            model_name=model_name,
            cache_dir=cache_dir,
            threads=threads,
            **kwargs
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.
        
        Args:
            texts: List of strings to embed.
            
        Returns:
            List of embedding vectors.
        """
        embeddings = list(self.embedding_model.embed(texts))
        return [e.tolist() for e in embeddings]

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.
        
        Args:
            text: Query string.
            
        Returns:
            Embedding vector.
        """
        # FastEmbed's embed method returns a generator
        embeddings = list(self.embedding_model.embed([text]))
        return embeddings[0].tolist()
