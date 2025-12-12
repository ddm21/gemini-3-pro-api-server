"""
Token counting utilities.

Extracts token usage information from Gemini API responses.
"""


def extract_token_counts(usage_metadata) -> tuple[int, int, int]:
    """Extract token counts from usage metadata.
    
    Args:
        usage_metadata: Usage metadata from API response
        
    Returns:
        tuple: (input_tokens, output_tokens, total_tokens)
    """
    def get_field(obj, *names, default=0):
        if obj is None:
            return default
        for name in names:
            value = getattr(obj, name, None)
            if value is not None:
                return value
        return default

    input_tokens = get_field(usage_metadata, "prompt_token_count", "promptTokenCount")
    output_tokens = get_field(usage_metadata, "candidates_token_count", "candidatesTokenCount")
    total_tokens = get_field(usage_metadata, "total_token_count", "totalTokenCount")
    
    return input_tokens, output_tokens, total_tokens
