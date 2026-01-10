"""
Default FastAPI server for strutex CLI.

Provides ready-to-use API endpoints for document extraction.
"""
import uvicorn
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Depends, Form
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

load_dotenv()

from .processor import DocumentProcessor
from .integrations.fastapi import get_processor, process_upload, ExtractionResponse
from .schemas import INVOICE_US

def create_app(
    provider: str = "gemini",
    model: str = "gemini-3-flash-preview",
    **kwargs
) -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Alias outer scope variables to avoid shadowing in inner functions
    default_provider = provider
    default_model = model

    app = FastAPI(
        title="Strutex Extraction API",
        description="Structured document extraction API powered by LLMs.",
        version="1.0.0"
    )

    # Configure processor dependency
    get_doc_processor = get_processor(
        provider=default_provider,
        model=default_model,
        **kwargs
    )

    @app.get("/", include_in_schema=False)
    def root():
        """Redirect root to docs."""
        return RedirectResponse(url="/docs")

    @app.get("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "ok", "service": "strutex-api"}

    @app.post("/extract", response_model=ExtractionResponse, tags=["Generic"])
    async def extract_generic(
        file: UploadFile = File(...),
        prompt: str = File("Extract data from this document."),
        json_schema: Optional[str] = File(
            '{"type": "object", "properties": {"summary": {"type": "string"}}}',
            description="JSON Schema string",
            alias="schema"
        ),
        provider: Optional[str] = Form(None, description="LLM Provider override"),
        model: Optional[str] = Form(None, description="Model name override"),
        processor: DocumentProcessor = Depends(get_doc_processor)
    ):
        """
        Generic document extraction endpoint.
        
        - **file**: Document PDF or Image
        - **prompt**: Instruction for the LLM
        - **schema**: Optional JSON Schema string for structured output
        - **provider**: Override default provider
        - **model**: Override default model
        
        **Example Schema:**
        ```json
        {
          "type": "object",
          "properties": {
            "title": {"type": "string"},
            "total_amount": {"type": "number"}
          }
        }
        ```
        """
        import json
        from .types import Schema

        # Handle overrides
        if provider or model:
            # Re-instantiate processor if overrides are present
            # Use aliased defaults from outer scope
            processor = DocumentProcessor(
                provider=provider or default_provider,
                model_name=model or default_model
            )

        async with process_upload(file) as tmp_path:
            try:
                # Parse schema if provided
                schema_obj = None
                if json_schema:
                    try:
                        schema_dict = json.loads(json_schema)
                        schema_obj = Schema.from_dict(schema_dict)
                    except json.JSONDecodeError as e:
                         return ExtractionResponse(
                            success=False,
                            error=f"Invalid JSON schema: {e}",
                            meta={"filename": file.filename}
                        )

                data = await processor.aprocess(
                    file_path=tmp_path,
                    prompt=prompt,
                    schema=schema_obj  # Passes generic schema to correct arg
                )
                
                # Handle return types
                result_data = data
                if hasattr(data, "model_dump"):
                    result_data = data.model_dump()
                elif hasattr(data, "to_dict"):
                    result_data = data.to_dict()

                return ExtractionResponse(
                    success=True,
                    data=result_data if isinstance(result_data, dict) else {"data": result_data},
                    meta={"filename": file.filename}
                )
                
            except Exception as e:
                return ExtractionResponse(
                    success=False,
                    error=str(e),
                    meta={"filename": file.filename}
                )

    @app.post("/extract/invoice", response_model=ExtractionResponse, tags=["Legacy"])
    async def extract_invoice(
        file: UploadFile = File(...),
        provider: Optional[str] = Form(None, description="LLM Provider override"),
        model: Optional[str] = Form(None, description="Model name override"),
        processor: DocumentProcessor = Depends(get_doc_processor)
    ):
        """
        (Legacy) Extract structured invoice data.
        Uses the default US Invoice schema.
        """
        # Handle overrides
        if provider or model:
            processor = DocumentProcessor(
                provider=provider or default_provider,
                model_name=model or default_model
            )

        async with process_upload(file) as tmp_path:
            try:
                data = await processor.aprocess(
                    file_path=tmp_path,
                    prompt="Extract invoice details.",
                    schema=INVOICE_US
                )
                
                return ExtractionResponse(
                    success=True,
                    data=data.model_dump(),
                    meta={"filename": file.filename}
                )
                
            except Exception as e:
                return ExtractionResponse(
                    success=False,
                    error=str(e),
                    meta={"filename": file.filename}
                )

    @app.post("/rag/ingest", tags=["RAG"])
    async def rag_ingest(
        file: UploadFile = File(...),
        collection: Optional[str] = Form(None, description="Collection name"),
        processor: DocumentProcessor = Depends(get_doc_processor)
    ):
        """
        Ingest a document into the RAG vector store.
        """
        async with process_upload(file) as tmp_path:
            try:
                processor.rag_ingest(tmp_path, collection_name=collection)
                return {"success": True, "message": f"Document '{file.filename}' ingested successfully."}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @app.post("/rag/query", response_model=ExtractionResponse, tags=["RAG"])
    async def rag_query(
        query: str = Form(..., description="Query or instruction"),
        collection: Optional[str] = Form(None, description="Collection name"),
        json_schema: Optional[str] = Form(
            None, 
            description="JSON Schema string for structured output",
            alias="schema"
        ),
        processor: DocumentProcessor = Depends(get_doc_processor)
    ):
        """
        Perform a RAG-based query/extraction.
        """
        import json
        from .types import Schema
        
        try:
            schema_obj = None
            if json_schema:
                schema_dict = json.loads(json_schema)
                schema_obj = Schema.from_dict(schema_dict)
                
            data = processor.rag_query(
                query=query,
                collection_name=collection,
                schema=schema_obj
            )
            
            return ExtractionResponse(
                success=True,
                data=data if isinstance(data, dict) else {"data": data},
                meta={"collection": collection or "default"}
            )
        except Exception as e:
            return ExtractionResponse(
                success=False,
                error=str(e),
                meta={"collection": collection or "default"}
            )

    return app

def start_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    provider: str = "gemini",
    model: str = "gemini-3-flash-preview"
):
    """Start the API server using uvicorn."""
    app = create_app(provider=provider, model=model)
    print(f"Starting Strutex API server on http://{host}:{port}")
    print(f"Provider: {provider} | Model: {model}")
    print(f"Docs available at http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)
