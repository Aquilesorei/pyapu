from strutex.types import Type

class SchemaAdapter:

    @staticmethod
    def to_google(strutex_schema):
        """Converts Strutex schema -> Google GenAI Schema"""
        from google.genai import types as g_types

        # Recursive conversion
        props = {k: SchemaAdapter.to_google(v) for k, v in
                 strutex_schema.properties.items()} if strutex_schema.properties else None
        items = SchemaAdapter.to_google(strutex_schema.items) if strutex_schema.items else None

        # Map Enum (Strutex Type -> Google Type)
        type_map = {
            Type.STRING: g_types.Type.STRING,
            Type.NUMBER: g_types.Type.NUMBER,
            Type.OBJECT: g_types.Type.OBJECT,
            Type.ARRAY: g_types.Type.ARRAY,
            Type.BOOLEAN: g_types.Type.BOOLEAN,
            Type.INTEGER: g_types.Type.INTEGER
        }

        return g_types.Schema(
            # FIX: Use the Enum directly, NOT .value
            type=type_map[strutex_schema.type],
            description=strutex_schema.description,
            properties=props,
            items=items,
            required=strutex_schema.required,
            nullable=strutex_schema.nullable
        )

    @staticmethod
    def to_openai(strutex_schema):
        """Converts Strutex schema -> OpenAI JSON Schema (Dict)"""
        schema_dict = {
            # OpenAI expects generic strings like "object", "string"
            "type": strutex_schema.type.value.lower(),
            "description": strutex_schema.description
        }

        if strutex_schema.properties:
            schema_dict["properties"] = {
                k: SchemaAdapter.to_openai(v) for k, v in strutex_schema.properties.items()
            }
            schema_dict["additionalProperties"] = False

        if strutex_schema.required:
            schema_dict["required"] = strutex_schema.required

        if strutex_schema.items:
            schema_dict["items"] = SchemaAdapter.to_openai(strutex_schema.items)

        return schema_dict