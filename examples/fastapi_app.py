"""
FastAPI Server Example for Strutex

Run with:
    pip install "strutex[server]"
    uvicorn examples.fastapi_app:app --reload

Features:
- Upload PDF/Image
- Extract to Pydantic Invoice model
- Swagger UI at http://localhost:8000/docs
- Fully async
"""

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from strutex import DocumentProcessor
from strutex.schemas import INVOICE_US
from strutex.integrations.fastapi import get_processor, process_upload, ExtractionResponse

app = FastAPI(title="Strutex Extraction API")

# Dependency: Creates a processor instance (configure provider here)
# For demo, using OpenAI. Ensure OPENAI_API_KEY is set.
get_doc_processor = get_processor(provider="openai", model="gpt-4o")

@app.post("/extract/invoice", response_model=ExtractionResponse)
async def extract_invoice(
    file: UploadFile = File(...),
    processor: DocumentProcessor = Depends(get_doc_processor)
):
    """
    Extract structured invoice data from an uploaded file.
    """
    async with process_upload(file) as tmp_path:
        try:
            # Async extraction using native async provider support
            data = await processor.aprocess(
                file_path=tmp_path,
                prompt="Extract invoice details.",
                model=INVOICE_US
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

@app.get("/")
def health_check():
    return {"status": "ok", "service": "strutex-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
