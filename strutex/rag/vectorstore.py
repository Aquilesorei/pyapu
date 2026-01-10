"""
Vector store service for strutex RAG.
Uses Qdrant for efficient similarity search.
"""
from typing import List, Optional, Dict, Any, Union
import uuid
import logging
from threading import Lock

logger = logging.getLogger("strutex.rag.vectorstore")

# Global registry to share Qdrant clients across processor instances in the same process.
# This avoids "Storage folder already accessed" errors when multiple processors point to the same disk path.
_QDRANT_CLIENTS: Dict[str, Any] = {}
_CLIENT_LOCK = Lock()

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from .embeddings import EmbeddingService


class QdrantVectorStore:
    """
    Vector store implementation using Qdrant.
    
    Supports local (in-memory or disk) and remote Qdrant instances.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        location: str = ":memory:",
        path: Optional[str] = None,
        url: Optional[str] = None,
        port: Optional[int] = 6333,
        api_key: Optional[str] = None,
        collection_name: str = "strutex_docs",
        **kwargs
    ):
        """
        Initialize the Qdrant vector store.
        
        Args:
            embedding_service: Service to generate embeddings.
            location: Qdrant location (e.g., ':memory:', 'http://localhost:6333').
            path: Path to local Qdrant database.
            url: Qdrant server URL.
            port: Qdrant server port.
            api_key: Qdrant API key for remote instances.
            collection_name: Default collection name.
        """
        if not QDRANT_AVAILABLE:
            raise ImportError(
                "qdrant-client is not installed. Please install it with: "
                "pip install 'strutex[rag]'"
            )

        self.embedding_service = embedding_service
        self.collection_name = collection_name
        
        # Determine unique key for this client
        client_key = str(path or url or location)
        
        with _CLIENT_LOCK:
            if client_key in _QDRANT_CLIENTS:
                logger.debug(f"Qdrant: Using existing shared client for {client_key}")
                self.client = _QDRANT_CLIENTS[client_key]
            else:
                logger.debug(f"Qdrant: Creating new client for {client_key}")
                self.client = QdrantClient(
                    location=location,
                    path=path,
                    url=url,
                    port=port,
                    api_key=api_key,
                    **kwargs
                )
                _QDRANT_CLIENTS[client_key] = self.client

    def _ensure_collection(self, collection_name: str, vector_size: int):
        """Ensure the collection exists with the correct vector size."""
        collections = self.client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        
        if not exists:
            logger.info(f"Qdrant: Creating collection '{collection_name}' (size={vector_size})")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        collection_name: Optional[str] = None
    ):
        """
        Add documents to the vector store.
        
        Args:
            texts: List of document contents.
            metadatas: Optional list of metadata dictionaries.
            collection_name: Collection to add documents to.
        """
        col_name = collection_name or self.collection_name
        logger.debug(f"Qdrant: Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_service.embed_documents(texts)
        
        if not embeddings:
            return

        vector_size = len(embeddings[0])
        self._ensure_collection(col_name, vector_size)
        
        points = []
        for i, (text, vector) in enumerate(zip(texts, embeddings)):
            metadata = metadatas[i] if metadatas else {}
            metadata["page_content"] = text
            
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=metadata
                )
            )
            
        logger.info(f"Qdrant: Upserting {len(points)} points into '{col_name}'")
        self.client.upsert(
            collection_name=col_name,
            points=points
        )

    def search(
        self,
        query: str,
        limit: int = 5,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: Query string.
            limit: Maximum number of results.
            collection_name: Collection to search in.
            
        Returns:
            List of dictionaries containing document content and metadata.
        """
        col_name = collection_name or self.collection_name
        query_vector = self.embedding_service.embed_query(query)
        
    def search(
        self,
        query: str,
        limit: int = 5,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: Query string.
            limit: Maximum number of results.
            collection_name: Collection to search in.
            
        Returns:
            List of dictionaries containing document content and metadata.
        """
        col_name = collection_name or self.collection_name
        logger.debug(f"Qdrant: Searching in collection '{col_name}' for: {query}")
        query_vector = self.embedding_service.embed_query(query)
        
        results = self.client.query_points(
            collection_name=col_name,
            query=query_vector,
            limit=limit
        ).points
        
        logger.info(f"Qdrant: Found {len(results)} results in '{col_name}'")
        
        return [
            {
                "content": hit.payload.get("page_content", ""),
                "metadata": {k: v for k, v in hit.payload.items() if k != "page_content"},
                "score": score if (score := getattr(hit, 'score', None)) is not None else 0.0
            }
            for hit in results
        ]
