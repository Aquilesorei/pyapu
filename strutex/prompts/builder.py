from typing import List, Dict, Optional, Any


class StructuredPrompt:
    """
    Builder for organizing complex extraction prompts.
    
    Provides a fluent API for constructing well-structured prompts with
    general rules, field-specific rules, and output guidelines.
    
    Usage:
        prompt = StructuredPrompt("You are an expert...")
        # Variadic arguments allow adding multiple rules at once
        prompt.add_general_rule("No guessing", "Use ISO dates")
        prompt.add_field_rule("total", "Exclude tax", "Must be numeric", critical=True)
        final_string = prompt.compile()
    
    Example:
        >>> prompt = (
        ...     StructuredPrompt()
        ...     .add_general_rule(
        ...         "Strict data fidelity: do not invent values.", 
        ...         "Dates must be in DD.MM.YYYY format."
        ...     )
        ...     .add_field_rule(
        ...         "artikelnummer", 
        ...         "Must be 8 digits.", 
        ...         "Ignore supplier codes.",
        ...         critical=True
        ...     )
        ...     .add_output_guideline("Return valid JSON.")
        ...     .compile()
        ... )
    """

    def __init__(self, persona: str = "You are a highly accurate AI Data Extraction Assistant."):
        """
        Initialize the prompt builder.
        
        Args:
            persona: The system persona/role description.
        """
        self.persona = persona.strip()
        self.general_rules: List[str] = []
        self.field_rules: Dict[str, List[str]] = {}
        self.output_guidelines: List[str] = []

    @classmethod
    def from_schema(cls, schema: Any, persona: Optional[str] = None) -> "StructuredPrompt":
        """
        Create a StructuredPrompt with field rules auto-generated from a Pydantic schema.
        
        Args:
            schema: A Pydantic BaseModel class with Field descriptions.
            persona: Optional custom persona string.
            
        Returns:
            A StructuredPrompt with field rules for each described field.
            
        Example:
            >>> from pydantic import BaseModel, Field
            >>> class Invoice(BaseModel):
            ...     invoice_number: str = Field(description="Unique invoice ID")
            ...     total: float = Field(description="Final amount due")
            >>> 
            >>> prompt = StructuredPrompt.from_schema(Invoice)
            >>> prompt.add_general_rule("Use ISO dates")
            >>> print(prompt.compile())
        """
        if persona:
            instance = cls(persona=persona)
        else:
            instance = cls()
        
        # Check if it's a Pydantic model
        if hasattr(schema, "model_fields"):
            # Pydantic v2
            for field_name, field_info in schema.model_fields.items():
                description = field_info.description
                if description:
                    # Mark required fields as critical
                    is_required = field_info.is_required()
                    instance.add_field_rule(field_name, description, critical=is_required)
        elif hasattr(schema, "__fields__"):
            # Pydantic v1 fallback
            for field_name, field_info in schema.__fields__.items():
                description = field_info.field_info.description
                if description:
                    is_required = field_info.required
                    instance.add_field_rule(field_name, description, critical=is_required)
        
        return instance

    def add_general_rule(self, *rules: str) -> "StructuredPrompt":
        """
        Adds one or more high-level rules.
        
        Args:
            *rules: Variable number of rule strings.
            
        Returns:
            Self for method chaining.
            
        Example:
            .add_general_rule("Rule 1", "Rule 2", "Rule 3")
        """
        self.general_rules.extend(rules)
        return self

    def add_field_rule(self, field_name: str, *rules: str, critical: bool = False) -> "StructuredPrompt":
        """
        Adds one or more rules specific to a single field.
        
        Args:
            field_name: The name of the field these rules apply to.
            *rules: Variable number of rule strings.
            critical: If True, prefixes rules with **CRITICAL**.
            
        Returns:
            Self for method chaining.
            
        Example:
            .add_field_rule("invoice_id", "Must be numeric", "8 digits", critical=True)
        """
        if field_name not in self.field_rules:
            self.field_rules[field_name] = []
        
        prefix = "**CRITICAL**: " if critical else ""
        for rule in rules:
            self.field_rules[field_name].append(f"{prefix}{rule}")
        return self

    def add_output_guideline(self, *guidelines: str) -> "StructuredPrompt":
        """
        Adds formatting instructions for the output.
        
        Args:
            *guidelines: Variable number of guideline strings.
            
        Returns:
            Self for method chaining.
            
        Example:
            .add_output_guideline("JSON only", "No markdown", "No comments")
        """
        self.output_guidelines.extend(guidelines)
        return self

    def compile(self) -> str:
        """
        Builds the final prompt string.
        
        Returns:
            The complete formatted prompt ready for LLM consumption.
        """
        parts = [self.persona, ""]

        if self.general_rules:
            parts.append("### 1. General Principles")
            parts.extend([f"- {r}" for r in self.general_rules])
            parts.append("")

        if self.field_rules:
            parts.append("### 2. Field Rules")
            for field, rules in self.field_rules.items():
                parts.append(f"\n**{field}**:")
                parts.extend([f"- {r}" for r in rules])
            parts.append("")

        parts.append("### 3. Output Format")
        if self.output_guidelines:
            parts.extend([f"- {r}" for r in self.output_guidelines])
        else:
            parts.append("- Output valid JSON only. No markdown.")

        return "\n".join(parts)

    def __str__(self) -> str:
        """Allow using the prompt directly as a string."""
        return self.compile()

    def __repr__(self) -> str:
        return (
            f"StructuredPrompt(general_rules={len(self.general_rules)}, "
            f"field_rules={len(self.field_rules)}, "
            f"output_guidelines={len(self.output_guidelines)})"
        )
