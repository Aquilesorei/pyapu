# API Reference

Complete reference for all public APIs.

---

## DocumentProcessor

::: strutex.processor.DocumentProcessor
options:
show_root_heading: true
members: - **init** - process

---

## Schema Types

::: strutex.types.String
options:
show_root_heading: true

::: strutex.types.Number
options:
show_root_heading: true

::: strutex.types.Integer
options:
show_root_heading: true

::: strutex.types.Boolean
options:
show_root_heading: true

::: strutex.types.Array
options:
show_root_heading: true

::: strutex.types.Object
options:
show_root_heading: true

---

## Plugin System

::: strutex.plugins.registry.PluginRegistry
options:
show_root_heading: true
members: - register - get - list - discover

::: strutex.plugins.registry.register
options:
show_root_heading: true

---

## Base Classes

::: strutex.plugins.base.Provider
options:
show_root_heading: true

::: strutex.plugins.base.Validator
options:
show_root_heading: true

::: strutex.plugins.base.Postprocessor
options:
show_root_heading: true

::: strutex.plugins.base.SecurityPlugin
options:
show_root_heading: true

---

## Security

::: strutex.security.chain.SecurityChain
options:
show_root_heading: true

::: strutex.security.sanitizer.InputSanitizer
options:
show_root_heading: true

::: strutex.security.injection.PromptInjectionDetector
options:
show_root_heading: true

::: strutex.security.output.OutputValidator
options:
show_root_heading: true

---

## Prompts

::: strutex.prompts.builder.StructuredPrompt
options:
show_root_heading: true
members: - **init** - add_general_rule - add_field_rule - add_output_guideline - compile

---

## Pydantic Support

::: strutex.pydantic_support.pydantic_to_schema
options:
show_root_heading: true

::: strutex.pydantic_support.validate_with_pydantic
options:
show_root_heading: true

---

## Exceptions

::: strutex.processor.SecurityError
options:
show_root_heading: true
