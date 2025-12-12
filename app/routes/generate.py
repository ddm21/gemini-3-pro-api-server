"""
Generate content endpoint.

Handles content generation with Gemini 3.0 Pro model.
Supports flexible prompts (text or file URLs), image URLs, and structured JSON output.
"""

import json
import logging

from fastapi import APIRouter, HTTPException

from google.genai import types

from app.config import MODEL_NAME, THINKING_ENABLED, THINKING_LEVEL, MAX_PROMPT_SIZE
from app.models import GenerateRequest, GenerateResponse
from app.dependencies import get_gemini_client
from app.utils import (
    load_content_from_source,
    load_image_from_url,
    convert_dict_to_schema,
    extract_token_counts,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Generation"])


def build_thinking_config() -> dict:
    """Build thinking config for Gemini 3.0 Pro.
    
    Returns:
        dict: Configuration with thinkingLevel (LOW, MEDIUM, or HIGH)
    """
    return {"thinkingLevel": THINKING_LEVEL if THINKING_ENABLED else "LOW"}


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate response from Gemini 3.0 Pro model.
    
    Accepts JSON requests with flexible prompt sources and image URLs.
    
    Args:
        request: GenerateRequest with:
            - user_prompt: REQUIRED - User's prompt (text or file URL)
            - user_prompt_type: Type ('text' or 'file'), defaults to 'text'
            - system_prompt: OPTIONAL - System instruction (text or file URL)
            - system_prompt_type: Type ('text' or 'file'), defaults to 'text'
            - image_urls: OPTIONAL - Array of image URLs
            - json_schema: OPTIONAL - Dict schema for structured output
        
    Returns:
        GenerateResponse: Output with token usage statistics
    """
    try:
        # 1. Load user prompt (REQUIRED)
        user_prompt_text = load_content_from_source(
            request.user_prompt, 
            request.user_prompt_type,
            max_size=MAX_PROMPT_SIZE
        )
        logger.info(f"Loaded user prompt ({request.user_prompt_type}): {len(user_prompt_text)} chars")
        
        # 2. Load system prompt (OPTIONAL)
        system_prompt_text = None
        if request.system_prompt:
            system_prompt_text = load_content_from_source(
                request.system_prompt,
                request.system_prompt_type,
                max_size=MAX_PROMPT_SIZE
            )
            logger.info(f"Loaded system prompt ({request.system_prompt_type}): {len(system_prompt_text)} chars")
        
        # 3. Process images from URLs
        parts: list[types.Part] = []
        
        if request.image_urls:
            for img_url in request.image_urls:
                img_bytes, mime_type = load_image_from_url(img_url)
                parts.append(types.Part.from_bytes(mime_type=mime_type, data=img_bytes))
                logger.info(f"Loaded image from URL: {img_url} ({mime_type}, {len(img_bytes)} bytes)")
        
        # 4. Add user prompt to parts
        parts.append(types.Part.from_text(text=user_prompt_text))
        
        # 5. Build request
        contents = [types.Content(role="user", parts=parts)]
        
        # 6. Build config
        config_params = {
            "temperature": 0.6,
            "top_p": 0.4,
            "max_output_tokens": 12000,
            "thinkingConfig": build_thinking_config(),
            "media_resolution": "MEDIA_RESOLUTION_MEDIUM",
        }
        
        # Add system instruction if provided
        if system_prompt_text:
            config_params["system_instruction"] = [types.Part.from_text(text=system_prompt_text)]
        
        # Add JSON schema if provided
        if request.json_schema:
            config_params["response_mime_type"] = "application/json"
            config_params["response_schema"] = convert_dict_to_schema(request.json_schema)
            logger.info("Using structured JSON output with schema")
        
        config = types.GenerateContentConfig(**config_params)
        
        # 7. Generate content
        client = get_gemini_client()
        logger.info(f"Generating content with model: {MODEL_NAME}")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=config,
        )
        
        # 8. Validate response
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
        
        # 9. Parse response
        try:
            parsed_output = json.loads(response.text)
        except json.JSONDecodeError:
            parsed_output = response.text
        except TypeError as e:
            logger.error(f"TypeError parsing response: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to parse response: {str(e)}")
        
        # 10. Extract token usage
        input_tokens, output_tokens, total_tokens = extract_token_counts(
            getattr(response, "usage_metadata", None)
        )
        
        # 11. Log usage
        has_schema = "structured" if request.json_schema else "natural"
        logger.info(
            f"[gemini-3-pro] mode={has_schema} "
            f"thinking={THINKING_ENABLED} level={THINKING_LEVEL if THINKING_ENABLED else 'LOW'} "
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
        raise HTTPException(status_code=500, detail=str(e))

