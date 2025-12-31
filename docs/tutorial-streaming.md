# Streaming

Get real-time feedback during extraction for better UX.

---

## Why Streaming?

For large documents, extraction can take 10-30 seconds. Streaming provides:

- **Progress feedback** — Users see something is happening
- **Early results** — Partial data before completion
- **Cancellation** — Stop extraction mid-way

---

## Basic Streaming

Use the `stream` parameter:

```python
from strutex import DocumentProcessor, GeminiProvider

processor = DocumentProcessor(provider=GeminiProvider())

# Stream extraction
for chunk in processor.stream(
    file_path="large_document.pdf",
    prompt="Extract all sections",
    schema=MySchema
):
    print(chunk, end="", flush=True)
```

---

## Streaming with Callbacks

Get structured updates during extraction:

```python
from strutex import DocumentProcessor, GeminiProvider

def on_chunk(chunk: str, context: dict):
    """Called for each streamed chunk."""
    print(f"Received: {chunk[:50]}...")

def on_complete(result: dict, context: dict):
    """Called when extraction completes."""
    print(f"Complete! Got {len(result)} fields")

processor = DocumentProcessor(provider=GeminiProvider())

result = processor.stream(
    file_path="document.pdf",
    prompt="Extract data",
    schema=MySchema,
    on_chunk=on_chunk,
    on_complete=on_complete
)
```

---

## Streaming in Web Apps

### FastAPI with SSE

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from strutex import DocumentProcessor, GeminiProvider

app = FastAPI()
processor = DocumentProcessor(provider=GeminiProvider())

@app.get("/extract/stream")
async def stream_extraction(file_path: str):
    async def generate():
        for chunk in processor.stream(file_path, "Extract", schema=MySchema):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### JavaScript Client

```javascript
const eventSource = new EventSource("/extract/stream?file_path=doc.pdf");

eventSource.onmessage = (event) => {
  if (event.data === "[DONE]") {
    eventSource.close();
    console.log("Extraction complete");
  } else {
    document.getElementById("output").innerHTML += event.data;
  }
};
```

---

## Progress Tracking

Track extraction progress for progress bars:

```python
from strutex import DocumentProcessor, GeminiProvider

processor = DocumentProcessor(provider=GeminiProvider())

total_chars = 0
estimated_total = 5000  # Estimate based on document size

for chunk in processor.stream("doc.pdf", "Extract", schema=MySchema):
    total_chars += len(chunk)
    progress = min(total_chars / estimated_total * 100, 99)
    print(f"\rProgress: {progress:.0f}%", end="")

print("\rProgress: 100%")
```

---

## Async Streaming

Use async streaming for better performance:

```python
import asyncio
from strutex import DocumentProcessor, GeminiProvider

processor = DocumentProcessor(provider=GeminiProvider())

async def stream_extract():
    async for chunk in processor.astream(
        file_path="document.pdf",
        prompt="Extract data",
        schema=MySchema
    ):
        print(chunk, end="", flush=True)

asyncio.run(stream_extract())
```

---

## Provider Support

| Provider          | Streaming Support |
| ----------------- | ----------------- |
| GeminiProvider    |  Full           |
| OpenAIProvider    |  Full           |
| AnthropicProvider |  Full           |
| OllamaProvider    |  Full           |
| GroqProvider      |  Limited        |
| ProviderChain     |  No             |

---

## Best Practices

| Practice                         | Why                           |
| -------------------------------- | ----------------------------- |
| Use streaming for docs > 5 pages | Better UX for long operations |
| Show loading indicator initially | Stream may take 1-2s to start |
| Handle connection drops          | Implement retry on disconnect |
| Buffer chunks on server          | Don't send every character    |

---

## Next Steps

| Want to...       | Go to...                                     |
| ---------------- | -------------------------------------------- |
| Handle errors    | [Error Handling](tutorial-error-handling.md) |
| See use cases    | [Use Cases](tutorial-use-cases.md)           |
| Optimize prompts | [Prompt Engineering](tutorial-prompts.md)    |
