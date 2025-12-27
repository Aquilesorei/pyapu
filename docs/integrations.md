# Framework Integrations

Strutex integrates with popular AI/ML frameworks, allowing you to use its structured extraction capabilities within existing pipelines.

## Installation

Install with integration extras:

```bash
# LangChain
pip install strutex[langchain]

# LlamaIndex
pip install strutex[llamaindex]

# Haystack
pip install strutex[haystack]

# Unstructured.io fallback
pip install strutex[fallback]

# All integrations
pip install strutex[all]
```

---

## LangChain

### StrutexLoader

Use Strutex as a LangChain document loader for structured extraction:

```python
from strutex.integrations import StrutexLoader
from strutex.schemas import INVOICE_US

# Load and extract structured data
loader = StrutexLoader(
    file_path="invoice.pdf",
    schema=INVOICE_US,
    provider="gemini"
)
documents = loader.load()

# Use in LangChain pipeline
print(documents[0].page_content)  # JSON string
print(documents[0].metadata)       # {"source": "invoice.pdf", "extractor": "strutex", ...}
```

### StrutexOutputParser

Validate LLM output against schemas:

```python
from strutex.integrations import StrutexOutputParser
from pydantic import BaseModel

class InvoiceData(BaseModel):
    vendor: str
    total: float
    date: str

parser = StrutexOutputParser(
    schema=InvoiceData,
    validators=["schema", "sum", "date"]  # Use strutex validators
)

# Parse LLM response
result = parser.parse(llm_response_text)
print(result.vendor)  # Validated Pydantic model

# Get format instructions for prompts
instructions = parser.get_format_instructions()
```

---

## LlamaIndex

### StrutexReader

Use Strutex as a LlamaIndex document reader:

```python
from strutex.integrations import StrutexReader
from strutex.schemas import INVOICE_GENERIC

reader = StrutexReader(
    schema=INVOICE_GENERIC,
    provider="openai"
)

documents = reader.load_data("invoice.pdf")

# Use with LlamaIndex index
from llama_index.core import VectorStoreIndex
index = VectorStoreIndex.from_documents(documents)
```

### StrutexNodeParser

Keep structured documents as single nodes (prevents chunking):

```python
from strutex.integrations import StrutexReader, StrutexNodeParser

reader = StrutexReader(schema=MySchema)
docs = reader.load_data("complex_doc.pdf")

# Don't chunk structured JSON
parser = StrutexNodeParser()
nodes = parser.get_nodes_from_documents(docs)
```

---

## Haystack

### StrutexConverter

Use Strutex in Haystack pipelines (coming soon):

```python
from strutex.integrations import StrutexConverter
from strutex.schemas import INVOICE_US

converter = StrutexConverter(schema=INVOICE_US)
documents = converter.run(file_path="invoice.pdf")
```

---

## Unstructured Fallback

### UnstructuredFallbackProcessor

Hybrid mode: use Strutex first, fall back to Unstructured.io if extraction fails:

```python
from strutex.integrations import UnstructuredFallbackProcessor
from strutex.schemas import INVOICE_US

processor = UnstructuredFallbackProcessor(
    schema=INVOICE_US,
    provider="gemini"
)

# Tries strutex first, falls back to unstructured.partition()
result = processor.process("messy_doc.pdf")
```

---

## DocumentInput

Handle both file paths and BytesIO (e.g., from HTTP uploads):

```python
from strutex import DocumentInput, DocumentProcessor
import io

# From file path
doc = DocumentInput("invoice.pdf")

# From in-memory bytes (e.g., HTTP request)
pdf_bytes = request.files['document'].read()
doc = DocumentInput(io.BytesIO(pdf_bytes), filename="upload.pdf")

# Use with processor
processor = DocumentProcessor(provider="gemini")
with doc.as_file_path() as path:
    result = processor.process(path, schema=MySchema)

# Or get raw bytes
content = doc.get_bytes()
mime = doc.get_mime_type()  # "application/pdf"
```

---

## Example: Full RAG Pipeline

Combine Strutex with LangChain for a complete RAG system:

```python
from strutex.integrations import StrutexLoader
from strutex.schemas import INVOICE_US
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# 1. Load and extract invoices
loader = StrutexLoader("invoices/*.pdf", schema=INVOICE_US)
docs = loader.load()

# 2. Create vector store
vectorstore = Chroma.from_documents(docs, OpenAIEmbeddings())

# 3. Build QA chain
qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(),
    retriever=vectorstore.as_retriever()
)

# 4. Query
answer = qa.invoke("Which invoice had the highest total?")
```
