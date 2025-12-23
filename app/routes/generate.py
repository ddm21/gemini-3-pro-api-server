"""
Generate content endpoint.

Handles content generation with Gemini 3.0 Pro model.
Supports flexible prompts (text or file URLs), image URLs, and structured JSON output.
"""

import json
import logging

from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from google.genai import types

from app.config import (
    MODEL_NAME, 
    MAX_PROMPT_SIZE, 
    SUPPORTED_MODELS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_MAX_OUTPUT_TOKENS,
    RATE_LIMIT
)
from app.models import GenerateRequest, GenerateResponse
from app.dependencies import get_gemini_client
from app.security import verify_api_key
from app.utils import (
    load_content_from_source,
    load_image_from_url,
    convert_dict_to_schema,
    extract_token_counts,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Generation"])
limiter = Limiter(key_func=get_remote_address)


def build_thinking_config(thinking_level: str, model: str) -> types.ThinkingConfig:
    """Build thinking config for Gemini 3.0 models.
    
    Args:
        thinking_level: Thinking level (case-insensitive)
        model: Model name to determine valid thinking levels
        
    Returns:
        types.ThinkingConfig: Configuration with thinking_level
    """
    from app.config import THINKING_LEVELS
    
    # Get valid levels for the model
    valid_levels = THINKING_LEVELS.get(model, ["LOW", "HIGH"])
    
    # Normalize thinking level to uppercase for enum
    level_upper = thinking_level.upper()
    
    # Map to ThinkingLevel enum
    if level_upper == "MINIMAL":
        thinking_enum = types.ThinkingLevel.MINIMAL
    elif level_upper == "LOW":
        thinking_enum = types.ThinkingLevel.LOW
    elif level_upper == "MEDIUM":
        thinking_enum = types.ThinkingLevel.MEDIUM
    elif level_upper == "HIGH":
        thinking_enum = types.ThinkingLevel.HIGH
    else:
        # Default based on model
        if model == "gemini-3-pro-preview":
            logger.warning(f"Invalid thinking_level '{thinking_level}' for {model}, defaulting to HIGH")
            thinking_enum = types.ThinkingLevel.HIGH
        else:
            logger.warning(f"Invalid thinking_level '{thinking_level}' for {model}, defaulting to HIGH")
            thinking_enum = types.ThinkingLevel.HIGH
    
    # Validate level is supported for the model
    if level_upper not in valid_levels:
        logger.warning(f"Thinking level '{level_upper}' may not be optimal for {model}")
    
    return types.ThinkingConfig(thinking_level=thinking_enum)


@router.post("/generate", response_model=GenerateResponse)
@limiter.limit(RATE_LIMIT)
async def generate(
    request: Request,
    data: GenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate response from Gemini 3.0 Pro model.
    
    Requires authentication via X-API-Key header.
    Rate limited to prevent abuse.
    
    Args:
        request: FastAPI request object
        data: GenerateRequest with:
            - user_prompt: REQUIRED - User's prompt (text or file URL)
            - user_prompt_type: Type ('text' or 'file'), defaults to 'text'
            - system_prompt: OPTIONAL - System instruction (text or file URL)
            - system_prompt_type: Type ('text' or 'file'), defaults to 'text'
            - image_urls: OPTIONAL - Array of image URLs
            - json_schema: OPTIONAL - Dict schema for structured output
        api_key: Validated API key from authentication
        
    Returns:
        GenerateResponse: Output with token usage statistics
    """
    try:
        # 1. Validate and select model
        selected_model = data.model if data.model else MODEL_NAME
        if selected_model not in SUPPORTED_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model '{selected_model}'. Supported models: {', '.join(SUPPORTED_MODELS)}"
            )
        logger.info(f"Using model: {selected_model}")
        
        # 2. Load user prompt (REQUIRED)
        user_prompt_text = load_content_from_source(
            data.user_prompt, 
            data.user_prompt_type,
            max_size=MAX_PROMPT_SIZE
        )
        logger.info(f"Loaded user prompt ({data.user_prompt_type}): {len(user_prompt_text)} chars")
        
        # 3. Load system prompt (OPTIONAL)
        system_prompt_text = None
        if data.system_prompt:
            system_prompt_text = load_content_from_source(
                data.system_prompt,
                data.system_prompt_type,
                max_size=MAX_PROMPT_SIZE
            )
            logger.info(f"Loaded system prompt ({data.system_prompt_type}): {len(system_prompt_text)} chars")
        
        # 4. Process images from URLs
        parts: list[types.Part] = []
        
        if data.image_urls:
            for img_url in data.image_urls:
                img_bytes, mime_type = load_image_from_url(img_url)
                parts.append(types.Part.from_bytes(mime_type=mime_type, data=img_bytes))
                logger.info(f"Loaded image from URL: {img_url} ({mime_type}, {len(img_bytes)} bytes)")
        
        # 5. Add user prompt to parts
        parts.append(types.Part.from_text(text=user_prompt_text))
        
        # 6. Build request
        contents = [types.Content(role="user", parts=parts)]
        
        # 7. Build config with request parameters
        # Validate and transform media_resolution
        valid_resolutions = ["LOW", "MEDIUM", "HIGH"]
        resolution = data.media_resolution.upper()
        if resolution not in valid_resolutions:
            logger.warning(f"Invalid media_resolution '{data.media_resolution}', defaulting to MEDIUM")
            resolution = "MEDIUM"
        media_res_full = f"MEDIA_RESOLUTION_{resolution}"
        
        config_params = {
            "temperature": DEFAULT_TEMPERATURE,
            "top_p": DEFAULT_TOP_P,
            "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            "thinking_config": build_thinking_config(data.thinking_level, selected_model),
            "media_resolution": media_res_full,
        }
        
        # Add system instruction if provided
        if system_prompt_text:
            config_params["system_instruction"] = [types.Part.from_text(text=system_prompt_text)]
        
        # Add JSON schema if provided
        if data.json_schema:
            config_params["response_mime_type"] = "application/json"
            config_params["response_schema"] = convert_dict_to_schema(data.json_schema)
            logger.info("Using structured JSON output with schema")
        
        config = types.GenerateContentConfig(**config_params)
        
        # 8. Generate content
        client = get_gemini_client()
        logger.info(f"Generating content with model: {selected_model}")
        response = client.models.generate_content(
            model=selected_model,
            contents=contents,
            config=config,
        )
        
        # 9. Validate response
        if not response or not hasattr(response, 'text'):
            logger.error("Invalid response from Gemini API")
            raise HTTPException(
                status_code=500,
                detail="Invalid response from Gemini API"
            )
        
        if response.text is None or response.text == "":
            logger.error(f"Empty response from Gemini API. Response: {response}")
            if hasattr(response, 'candidates') and response.candidates:
                logger.error(f"Candidates: {response.candidates}")
            raise HTTPException(
                status_code=500,
                detail="Gemini API returned empty response (content filtering or safety block)"
            )
        
        # 10. Parse response
        try:
            parsed_output = json.loads(response.text)
        except json.JSONDecodeError:
            parsed_output = response.text
        except TypeError as e:
            logger.error(f"TypeError parsing response: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to parse response: {str(e)}")
        
        # 11. Extract token usage
        input_tokens, output_tokens, total_tokens = extract_token_counts(
            getattr(response, "usage_metadata", None)
        )
        
        # 12. Log usage
        has_schema = "structured" if data.json_schema else "natural"
        model_short = selected_model.replace("-preview", "").replace("gemini-", "")
        logger.info(
            f"[{model_short}] mode={has_schema} "
            f"thinking_level={data.thinking_level} "
            f"media_res={resolution} "
            f"tokens={input_tokens}/{output_tokens}/{total_tokens}"
        )
        
        return GenerateResponse(
            output=parsed_output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        # Don't expose internal error details to clients
        raise HTTPException(
            status_code=500, 
            detail="An internal error occurred. Please contact support if this persists."
        )

