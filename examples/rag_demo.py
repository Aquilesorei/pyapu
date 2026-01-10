"""
Demonstration of RAG capabilities in strutex.
"""
import os
import json
from strutex import DocumentProcessor, Schema, Object, String, Number

# Initialize processor
# Make sure you have GOOGLE_API_KEY or other provider keys in your .env
processor = DocumentProcessor(provider="gemini")

def run_demo():
    # 1. Prepare a sample document
    # For this demo, we'll create a simple text file if it doesn't exist
    doc_path = "sample_knowledge.txt"
    with open(doc_path, "w") as f:
        f.write("""
        The ACME Corporation was founded in 1947 by Wile E. Coyote.
        Its headquarters are located in Albuquerque, New Mexico.
        In 2023, the total revenue was $5.2 billion.
        The CEO is currently Road Runner.
        """)

    try:
        # 2. Ingest document into RAG
        print(f"Ingesting {doc_path} into RAG...")
        processor.rag_ingest(doc_path, collection_name="acme_corp")

        # 3. Query the RAG
        query = "Who founded ACME and what was the revenue in 2023?"
        print(f"\nQuerying: {query}")
        
        # Define a schema for structured extraction from the query
        schema = Object(properties={
            "founder": String(),
            "revenue_2023": String()
        })
        
        result = processor.rag_query(
            query=query,
            collection_name="acme_corp",
            schema=schema
        )
        
        print("\nExtracted Result:")
        print(json.dumps(result, indent=2))

    finally:
        # Cleanup
        if os.path.exists(doc_path):
            os.remove(doc_path)

if __name__ == "__main__":
    run_demo()
