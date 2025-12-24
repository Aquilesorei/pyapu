"""
Tests for strutex.prompts.builder module.
"""

import pytest
import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from strutex.prompts.builder import StructuredPrompt


class TestStructuredPromptInit:
    """Tests for StructuredPrompt initialization."""

    def test_default_persona(self):
        """Test default persona is set."""
        prompt = StructuredPrompt()
        assert "AI Data Extraction Assistant" in prompt.persona

    def test_custom_persona(self):
        """Test custom persona."""
        prompt = StructuredPrompt(persona="You are an expert invoice reader.")
        assert prompt.persona == "You are an expert invoice reader."

    def test_persona_strips_whitespace(self):
        """Test persona whitespace is stripped."""
        prompt = StructuredPrompt(persona="  Custom persona  ")
        assert prompt.persona == "Custom persona"

    def test_empty_initial_state(self):
        """Test initial state has empty lists."""
        prompt = StructuredPrompt()
        assert prompt.general_rules == []
        assert prompt.field_rules == {}
        assert prompt.output_guidelines == []


class TestAddGeneralRule:
    """Tests for add_general_rule method."""

    def test_single_rule(self):
        """Test adding a single rule."""
        prompt = StructuredPrompt()
        prompt.add_general_rule("Rule 1")
        assert prompt.general_rules == ["Rule 1"]

    def test_multiple_rules_variadic(self):
        """Test adding multiple rules in one call (variadic)."""
        prompt = StructuredPrompt()
        prompt.add_general_rule("Rule 1", "Rule 2", "Rule 3")
        assert prompt.general_rules == ["Rule 1", "Rule 2", "Rule 3"]

    def test_chaining(self):
        """Test method returns self for chaining."""
        prompt = StructuredPrompt()
        result = prompt.add_general_rule("Rule 1")
        assert result is prompt

    def test_multiple_calls_accumulate(self):
        """Test multiple calls accumulate rules."""
        prompt = StructuredPrompt()
        prompt.add_general_rule("Rule 1")
        prompt.add_general_rule("Rule 2", "Rule 3")
        assert prompt.general_rules == ["Rule 1", "Rule 2", "Rule 3"]


class TestAddFieldRule:
    """Tests for add_field_rule method."""

    def test_single_field_rule(self):
        """Test adding a single field rule."""
        prompt = StructuredPrompt()
        prompt.add_field_rule("invoice_id", "Must be numeric")
        assert "invoice_id" in prompt.field_rules
        assert prompt.field_rules["invoice_id"] == ["Must be numeric"]

    def test_multiple_rules_same_field(self):
        """Test adding multiple rules to same field (variadic)."""
        prompt = StructuredPrompt()
        prompt.add_field_rule("total", "Must be positive", "Exclude tax")
        assert prompt.field_rules["total"] == ["Must be positive", "Exclude tax"]

    def test_critical_flag(self):
        """Test critical flag adds prefix."""
        prompt = StructuredPrompt()
        prompt.add_field_rule("amount", "Must be exact", critical=True)
        assert prompt.field_rules["amount"] == ["**CRITICAL**: Must be exact"]

    def test_critical_multiple_rules(self):
        """Test critical flag applies to all rules in call."""
        prompt = StructuredPrompt()
        prompt.add_field_rule("id", "Rule 1", "Rule 2", critical=True)
        assert prompt.field_rules["id"] == [
            "**CRITICAL**: Rule 1",
            "**CRITICAL**: Rule 2"
        ]

    def test_accumulate_rules_same_field(self):
        """Test multiple calls to same field accumulate."""
        prompt = StructuredPrompt()
        prompt.add_field_rule("date", "Format DD.MM.YYYY")
        prompt.add_field_rule("date", "Must be in the past")
        assert prompt.field_rules["date"] == [
            "Format DD.MM.YYYY",
            "Must be in the past"
        ]

    def test_chaining(self):
        """Test method returns self for chaining."""
        prompt = StructuredPrompt()
        result = prompt.add_field_rule("field", "rule")
        assert result is prompt


class TestAddOutputGuideline:
    """Tests for add_output_guideline method."""

    def test_single_guideline(self):
        """Test adding a single guideline."""
        prompt = StructuredPrompt()
        prompt.add_output_guideline("Return JSON only")
        assert prompt.output_guidelines == ["Return JSON only"]

    def test_multiple_guidelines_variadic(self):
        """Test adding multiple guidelines in one call."""
        prompt = StructuredPrompt()
        prompt.add_output_guideline("JSON only", "No markdown", "No comments")
        assert prompt.output_guidelines == ["JSON only", "No markdown", "No comments"]

    def test_chaining(self):
        """Test method returns self for chaining."""
        prompt = StructuredPrompt()
        result = prompt.add_output_guideline("Guideline")
        assert result is prompt


class TestCompile:
    """Tests for compile method."""

    def test_compile_persona_only(self):
        """Test compile with only persona."""
        prompt = StructuredPrompt(persona="Test persona")
        result = prompt.compile()
        assert result.startswith("Test persona")
        # Should have default output format
        assert "### 3. Output Format" in result
        assert "Output valid JSON only" in result

    def test_compile_with_general_rules(self):
        """Test compile includes general rules section."""
        prompt = StructuredPrompt()
        prompt.add_general_rule("Rule A", "Rule B")
        result = prompt.compile()
        assert "### 1. General Principles" in result
        assert "- Rule A" in result
        assert "- Rule B" in result

    def test_compile_with_field_rules(self):
        """Test compile includes field rules section."""
        prompt = StructuredPrompt()
        prompt.add_field_rule("invoice", "Must exist", critical=True)
        result = prompt.compile()
        assert "### 2. Field Rules" in result
        assert "**invoice**:" in result
        assert "- **CRITICAL**: Must exist" in result

    def test_compile_with_output_guidelines(self):
        """Test compile includes custom output guidelines."""
        prompt = StructuredPrompt()
        prompt.add_output_guideline("Custom guideline")
        result = prompt.compile()
        assert "### 3. Output Format" in result
        assert "- Custom guideline" in result
        # Default should NOT appear
        assert "Output valid JSON only. No markdown." not in result

    def test_compile_full_prompt(self):
        """Test compile with all sections."""
        prompt = (
            StructuredPrompt(persona="Expert extractor")
            .add_general_rule("Be accurate")
            .add_field_rule("id", "8 digits")
            .add_output_guideline("JSON only")
        )
        result = prompt.compile()

        assert "Expert extractor" in result
        assert "### 1. General Principles" in result
        assert "### 2. Field Rules" in result
        assert "### 3. Output Format" in result


class TestStringMethods:
    """Tests for __str__ and __repr__ methods."""

    def test_str_equals_compile(self):
        """Test __str__ returns same as compile."""
        prompt = StructuredPrompt().add_general_rule("Test")
        assert str(prompt) == prompt.compile()

    def test_repr(self):
        """Test __repr__ shows counts."""
        prompt = (
            StructuredPrompt()
            .add_general_rule("R1", "R2")
            .add_field_rule("f1", "r1")
            .add_field_rule("f2", "r2")
            .add_output_guideline("g1")
        )
        r = repr(prompt)
        assert "general_rules=2" in r
        assert "field_rules=2" in r
        assert "output_guidelines=1" in r


class TestFluentChaining:
    """Tests for fluent API chaining."""

    def test_full_chain(self):
        """Test complete fluent chain."""
        result = (
            StructuredPrompt()
            .add_general_rule("G1", "G2")
            .add_field_rule("f1", "r1", "r2", critical=True)
            .add_field_rule("f2", "r3")
            .add_output_guideline("O1", "O2")
            .compile()
        )

        assert isinstance(result, str)
        assert "G1" in result
        assert "**CRITICAL**" in result
        assert "O1" in result
if __name__ == "__main__":
    pytest.main([__file__, "-v"])