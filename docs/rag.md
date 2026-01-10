# Retrieval-Augmented Generation (RAG)

Strutex provides a built-in RAG system that allows you to index documents and perform structured queries against a knowledge base. This is particularly useful for extracting data from large sets of documents or when the answer requires cross-referencing information that doesn't fit in a single LLM context window.

## Architecture

The RAG system in Strutex is built with three main components:

1.  **Embedding Service**: Uses `FastEmbed` for fast, local embedding generation. No API keys are required for embeddings by default.
2.  **Vector Store**: Uses `Qdrant` for efficient similarity search. It supports in-memory, local disk, and remote Qdrant instances.
3.  **RAG Engine**: Orchestrates the retrieval and generation flow using `LangGraph`.

## Installation

To use RAG features, install the `rag` extra:

```bash
pip install "strutex[rag]"
```

## Basic Usage

### Ingesting Documents

You can ingest any document supported by Strutex into the vector store.

```python
from strutex import DocumentProcessor

processor = DocumentProcessor(provider="gemini")

# Indexing a document
processor.rag_ingest("company_policy.pdf", collection_name="knowledge_base")
```

### Querying with Structured Extraction

Once documents are indexed, you can perform queries that return structured data.

```python
from strutex import DocumentProcessor, Object, String

processor = DocumentProcessor(provider="gemini")

schema = Object(properties={
    "policy_name": String(),
    "max_reimbursement": String()
})

result = processor.rag_query(
    query="What is the travel reimbursement policy?",
    schema=schema,
    collection_name="knowledge_base"
)

print(result)
```

## CLI Usage

The CLI provides commands for managing the RAG vector store.

### Ingest

```bash
strutex rag ingest company_policy.pdf --collection knowledge_base
```

### Query

```bash
strutex rag query "What is the travel reimbursement policy?" --collection knowledge_base
```

## API Usage

When running the Strutex server (`strutex serve`), the following endpoints are available:

- `POST /rag/ingest`: Upload a file to ingest into a collection.
- `POST /rag/query`: Perform a RAG query and get structured JSON output.

## Configuration

The default RAG configuration uses:

- **Embeddings**: `BAAI/bge-small-en-v1.5` (via FastEmbed)
- **Vector Store**: In-memory Qdrant instance

You can customize these by configuring the `DocumentProcessor` or using explicit service instances.
