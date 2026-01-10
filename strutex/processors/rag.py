"""
RAG Processor - Retrieval-Augmented Generation.

This processor uses a vector store to retrieve relevant context before
generating structured output.
"""

import json
import logging
import os
from typing import Any, Optional, Type

from .base import Processor
from ..documents import get_mime_type
from ..types import Schema

logger = logging.getLogger(__name__)
class RagProcessor(Processor):
    """
    Retrieval-Augmented Generation processor.
    
    Uses a vector store (Qdrant) and embeddings (FastEmbed) to retrieve
    relevant context from indexed documents before generating structured output.
    
    Example:
        ```python
        from strutex.processors import RagProcessor
        from strutex import Object, String
        
        processor = RagProcessor(provider="gemini")
        
        processor.ingest("manual.pdf", collection="docs")
        processor.ingest("faq.pdf", collection="docs")
        
        schema = Object(properties={"answer": String()})
        result = processor.query("How to reset device?", collection="docs", schema=schema)
        ```
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rag_engine: Optional[Any] = None
    
    def _get_engine(self) -> Any:
        """Lazy-initialize the RAG engine."""
        if self._rag_engine is None:
            from ..rag.embeddings import FastEmbedService
            from ..rag.vectorstore import QdrantVectorStore
            from ..rag.engine import RagEngine
            
            embeddings = FastEmbedService()
            
            # Use disk persistence by default for RAG to ensure data survives across requests/restarts
            rag_path = os.environ.get(
                "STRUTEX_RAG_PATH", 
                os.path.expanduser("~/.cache/strutex/rag_data")
            )
            os.makedirs(rag_path, exist_ok=True)
            
            vector_store = QdrantVectorStore(
                embedding_service=embeddings,
                location=None,  # Set to None so it uses the 'path' argument
                path=rag_path
            )
            self._rag_engine = RagEngine(vector_store=vector_store, processor=self)
        
        return self._rag_engine
    
    def ingest(self, file_path: str, collection: Optional[str] = None) -> None:
        """
        Ingest a document into the vector store.
        
        Args:
            file_path: Path to the document.
            collection: Collection name.
        """
        logger.info(f"RAG: Ingesting document '{file_path}' into collection '{collection or 'default'}'")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        engine = self._get_engine()
        mime_type = get_mime_type(file_path)
        text = self._extract_source_text(file_path, mime_type)
        
        if text:
            logger.debug(f"RAG: Extracted {len(text)} characters of text from {file_path}")
            chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
            logger.info(f"RAG: Adding {len(chunks)} chunks to vector store.")
            engine.vector_store.add_documents(
                texts=chunks,
                metadatas=[{"source": file_path} for _ in chunks],
                collection_name=collection
            )
        else:
            logger.warning(f"RAG: No text extracted from {file_path}")
    
    def query(
        self,
        query: str,
        collection: Optional[str] = None,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        top_k: int = 5
    ) -> Any:
        """
        Perform a RAG query.
        
        Args:
            query: User query.
            collection: Collection to search.
            schema: Output schema.
            model: Pydantic model for output.
            top_k: Number of retrieved chunks.
            
        Returns:
            Extracted result.
        """
        logger.info(f"RAG: Querying collection '{collection or 'default'}': {query} (top_k={top_k})")
        engine = self._get_engine()
        
        pydantic_schema, pydantic_model = self._convert_pydantic(model)
        if pydantic_schema:
            schema = pydantic_schema
        
        schema_instructions = ""
        if schema:
            schema_instructions = f"Return the result as a JSON object matching this schema: {json.dumps(schema.to_dict())}"
        
        result = engine.query(
            query,
            schema_instructions=schema_instructions,
            collection_name=collection,
            schema=schema,
            top_k=top_k
        )
        
        extracted = result.get("answer")
        return self._validate_pydantic(extracted, pydantic_model)
    
    async def aquery(
        self,
        query: str,
        collection: Optional[str] = None,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        top_k: int = 5
    ) -> Any:
        """
        Perform an asynchronous RAG query.
        """
        logger.info(f"RAG: Async Querying collection '{collection or 'default'}': {query} (top_k={top_k})")
        engine = self._get_engine()
        
        pydantic_schema, pydantic_model = self._convert_pydantic(model)
        if pydantic_schema:
            schema = pydantic_schema
        
        schema_instructions = ""
        if schema:
            schema_instructions = f"Return the result as a JSON object matching this schema: {json.dumps(schema.to_dict())}"
        
        result = await engine.aquery(
            query,
            schema_instructions=schema_instructions,
            collection_name=collection,
            schema=schema,
            top_k=top_k
        )
        
        extracted = result.get("answer")
        return self._validate_pydantic(extracted, pydantic_model)
    
    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        **kwargs
    ) -> Any:
        """
        RAG-based processing: ingest then query.
        
        This is a convenience method that ingests the document and then
        queries for the given prompt.
        
        Args:
            file_path: Path to the document.
            prompt: Query/extraction prompt.
            schema: Output schema.
            model: Pydantic model for output.
            **kwargs: Additional options.
            
        Returns:
            Extracted result.
        """
        collection = kwargs.get("collection", "default")
        self.ingest(file_path, collection=collection)
        return self.query(prompt, collection=collection, schema=schema, model=model)
    
    async def aprocess(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        **kwargs
    ) -> Any:
        """
        Async RAG-based processing.
        """
        collection = kwargs.get("collection", "default")
        # Keep ingestion as a background task if needed, but here we wait for it
        import asyncio
        await asyncio.to_thread(self.ingest, file_path, collection=collection)
        return await self.aquery(prompt, collection=collection, schema=schema, model=model)
