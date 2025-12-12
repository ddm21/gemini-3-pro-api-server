"""
JSON Schema conversion utilities.

Converts dictionary-based JSON schemas to Gemini API types.Schema format.
"""

from google.genai import types


def convert_dict_to_schema(schema_dict: dict) -> types.Schema:
    """Convert a dictionary JSON schema to genai.types.Schema format.
    
    Args:
        schema_dict: Dictionary representation of JSON schema
        
    Returns:
        types.Schema: Properly formatted Schema object
    """
    type_mapping = {
        "string": types.Type.STRING,
        "number": types.Type.NUMBER,
        "integer": types.Type.INTEGER,
        "boolean": types.Type.BOOLEAN,
        "object": types.Type.OBJECT,
        "array": types.Type.ARRAY,
    }
    
    schema_type = schema_dict.get("type", "object")
    genai_type = type_mapping.get(schema_type, types.Type.OBJECT)
    
    schema_params = {"type": genai_type}
    
    # Handle properties for OBJECT type
    if schema_type == "object" and "properties" in schema_dict:
        properties = {}
        for prop_name, prop_schema in schema_dict["properties"].items():
            properties[prop_name] = convert_dict_to_schema(prop_schema)
        schema_params["properties"] = properties
    
    # Handle required fields
    if "required" in schema_dict:
        schema_params["required"] = schema_dict["required"]
    
    # Handle items for ARRAY type
    if schema_type == "array" and "items" in schema_dict:
        schema_params["items"] = convert_dict_to_schema(schema_dict["items"])
    
    # Handle description
    if "description" in schema_dict:
        schema_params["description"] = schema_dict["description"]
    
    return types.Schema(**schema_params)
