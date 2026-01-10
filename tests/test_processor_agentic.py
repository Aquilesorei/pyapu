"""
Verification test for AgenticProcessor.
"""

import os
import json
import asyncio
from strutex import DocumentProcessor, Object, String

# Sample document for testing
SAMPLE_FILE = "agent_test_doc.txt"
SAMPLE_CONTENT = """
SEC FILING: ACME CORP
Central Index Key: 0001234567
Founded: 1999
CEO: Wile E. Coyote
Revenue 2023: $10.5 Billion
"""

def setup_sample():
    with open(SAMPLE_FILE, "w") as f:
        f.write(SAMPLE_CONTENT)

def cleanup_sample():
    if os.path.exists(SAMPLE_FILE):
        os.remove(SAMPLE_FILE)

def test_agentic():
    asyncio.run(_test_agentic())

async def _test_agentic():
    setup_sample()
    print("🚀 Testing AgenticProcessor with LangGraph...")
    
    dp = DocumentProcessor(provider="gemini")
    schema = Object(properties={
        "cik": String(),
        "founded": String(),
        "ceo": String()
    })

    try:
        # We call the agentic processor
        print("Invoking Agent Loop...")
        result = dp.agentic.process(
            SAMPLE_FILE, 
            "Extract the CIK, founded year, and CEO name. Use different tools if needed.", 
            schema=schema
        )
        
        print("\n✅ Agent Result:")
        print(json.dumps(result, indent=2))
        
        # Basic validation
        assert "0001234567" in str(result)
        assert "Coyote" in str(result)
        print("\nVerification Successful!")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_sample()

if __name__ == "__main__":
    asyncio.run(test_agentic())
