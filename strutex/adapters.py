from strutex.types import Type

class SchemaAdapter:

    @staticmethod
    def to_google(schema):
        """Converts Strutex schema -> Google GenAI Schema"""
        from google.genai import types as g_types

        # Recursive conversion
        props = {k: SchemaAdapter.to_google(v) for k, v in
                 schema.properties.items()} if schema.properties else None
        items = SchemaAdapter.to_google(schema.items) if schema.items else None

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
            type=type_map[schema.type],
            description=schema.description,
            properties=props,
            items=items,
            required=schema.required,
            nullable=schema.nullable
        )

    @staticmethod
    def to_openai(schema):
        """Converts Strutex schema -> OpenAI JSON Schema (Dict)"""
        schema_dict = {
            # OpenAI expects generic strings like "object", "string"
            "type": schema.type.value.lower(),
            "description": schema.description
        }

        if schema.properties:
            schema_dict["properties"] = {
                k: SchemaAdapter.to_openai(v) for k, v in schema.properties.items()
            }
            schema_dict["additionalProperties"] = False

        if schema.required:
            schema_dict["required"] = schema.required

        if schema.items:
            schema_dict["items"] = SchemaAdapter.to_openai(schema.items)

        return schema_dict

    @staticmethod
    def to_json_schema(schema):
        """Converts Strutex schema -> Standard JSON Schema"""
        # OpenAI format is compatible enough for standard usage
        return SchemaAdapter.to_openai(schema)