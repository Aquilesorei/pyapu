"""
LangChain integration for Strutex.
Allows using Strutex as a DocumentLoader within the LangChain ecosystem.
"""
import json
from typing import List, Optional, Type, Any, Dict, Union

from strutex import Schema

# Attempt to import LangChain core components.
# This makes LangChain an optional dependency.
try:
    from langchain_core.document_loaders import BaseLoader
    from langchain_core.documents import Document
except ImportError:
    # Fallback for older LangChain versions or missing installation
    raise ImportError(
        "Could not import langchain_core. "
        "Please install langchain to use StrutexLoader: pip install langchain"
    )

from strutex.processor import DocumentProcessor
from strutex.plugins.base import Provider


class StrutexLoader(BaseLoader):
    """
    A LangChain-compatible loader that uses Strutex to extract structured data
    from documents (PDF, Images) and returns them as LangChain Documents.
    """

    def __init__(
        self,
        file_path: str,
        schema: Schema,
        prompt : Optional[str] = None,
        provider: Union[str, Provider] = "gemini",
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the StrutexLoader.

        Args:
            file_path: Path to the file to process.
            schema: The Pydantic model or schema class to validate extraction against.
            provider: The AI provider to use (e.g., 'gemini', 'openai').
            api_key: Optional API key for the provider.
            config: Extra configuration for the processor.
        """
        self.file_path = file_path
        self.schema = schema
        self.prompt = prompt or ""
        # Initialize the Strutex processor
        self.processor = DocumentProcessor(
            provider=provider,
            api_key=api_key,
            **(config or {})
        )

    def load(self) -> List[Document]:
        """
        Process the file using Strutex and return a list containing a single
        LangChain Document with the JSON result.
        """
        return list(self.lazy_load())

    def lazy_load(self):
        """
        Lazy load implementation. Efficient for processing large batches if needed later.
        """
        result = self.processor.process(
            file_path=self.file_path,
            prompt=self.prompt,
            schema=self.schema,

        )

        # 2. Convert the Pydantic model (or dict) to a JSON string
        # We handle both Pydantic models (model_dump) and raw dicts
        if hasattr(result, "model_dump"):
            data_dict = result.model_dump()
            content_str = result.model_dump_json(indent=2)
        else:
            data_dict = result if isinstance(result, dict) else {"data": str(result)}
            content_str = json.dumps(data_dict, indent=2)

        # 3. Build Metadata for RAG filtering
        metadata = {
            "source": self.file_path,
            "extractor": "strutex",
            "provider": self.processor.provider_name
        }

        # Optional: Lift specific top-level fields to metadata for better filtering
        # E.g., if the schema has a 'date' or 'category', put it in metadata too.
        for key in ["date", "category", "type", "invoice_number"]:
            if key in data_dict:
                metadata[key] = data_dict[key]

        # 4. Yield the LangChain Document
        yield Document(
            page_content=content_str,
            metadata=metadata
        )


class StrutexOutputParser:
    """
    A LangChain-compatible output parser that validates LLM text output
    using Strutex's validation infrastructure.
    
    Unlike basic JSON parsers, this uses Strutex's SchemaValidator for
    robust validation with detailed error messages.
    
    Example:
        parser = StrutexOutputParser(schema=InvoiceSchema)
        result = parser.parse(llm_output_text)
        
        # With custom validation chain
        parser = StrutexOutputParser(
            schema=InvoiceSchema,
            validators=["schema", "sum", "date"]
        )
    """

    def __init__(
        self,
        schema: Schema,
        validators: Optional[List[str]] = None,
        provider: Union[str, Provider] = "gemini",
        api_key: Optional[str] = None
    ):
        """
        Initialize the output parser.

        Args:
            schema: A Pydantic model or Strutex schema to validate against.
            validators: List of validator names to apply (e.g., ["schema", "sum"]).
                        Defaults to ["schema"] if not specified.
            provider: Provider to use for re-extraction if parsing fails.
            api_key: Optional API key for the provider.
        """
        self.schema = schema
        self.validators = validators or ["schema"]
        
        # Initialize processor for potential re-extraction
        self.processor = DocumentProcessor(
            provider=provider,
            api_key=api_key
        )
        
        # Build validation chain from strutex validators
        from strutex.validators import SchemaValidator, SumValidator, DateValidator, ValidationChain
        
        validator_map = {
            "schema": SchemaValidator,
            "sum": SumValidator,
            "date": DateValidator,
        }
        
        chain_validators = []
        for v in self.validators:
            if v in validator_map:
                chain_validators.append(validator_map[v]())
        
        self.validation_chain = ValidationChain(chain_validators) if chain_validators else None
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from LLM output, handling markdown code blocks."""
        text = text.strip()
        
        # Handle markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            text = text.strip()
        
        return text
    
    def parse(self, text: str) -> Any:
        """
        Parse LLM output text into a validated schema instance.

        Args:
            text: Raw text output from an LLM (expected to be JSON).

        Returns:
            Validated Pydantic model instance or dict.

        Raises:
            ValueError: If the text cannot be parsed or fails validation.
        """
        json_text = self._extract_json(text)
        
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM output as JSON: {e}")
        
        # Run through validation chain if configured
        if self.validation_chain:
            is_valid, errors = self.validation_chain.validate(data, self.schema)
            if not is_valid:
                raise ValueError(f"Validation failed: {errors}")
        
        # Validate against Pydantic schema
        if hasattr(self.schema, "model_validate"):
            return self.schema.model_validate(data)
        elif hasattr(self.schema, "parse_obj"):  # Pydantic v1
            return self.schema.parse_obj(data)
        else:
            return data
    
    def get_format_instructions(self) -> str:
        """
        Return format instructions for the LLM to generate valid output.
        Uses strutex's prompt building infrastructure.
        """
        from strutex.prompts.builder import StructuredPrompt
        from strutex.pydantic_support import pydantic_to_schema
        
        # Convert Pydantic model to strutex schema if needed
        if hasattr(self.schema, "model_json_schema"):
            schema_dict = self.schema.model_json_schema()
            return (
                "Respond with a JSON object that conforms to this schema:\n"
                f"```json\n{json.dumps(schema_dict, indent=2)}\n```"
            )
        else:
            return "Respond with valid JSON matching the expected structure."