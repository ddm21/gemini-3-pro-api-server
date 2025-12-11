import os
import json
import logging
import mimetypes
from typing import Union
from functools import lru_cache
from contextlib import asynccontextmanager
from datetime import datetime

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load environment variables
load_dotenv()

# API Configuration
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY not set in env or .env")

# Thinking Configuration
THINKING_ENABLED = os.getenv("THINKING_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
THINKING_LEVEL = os.getenv("THINKING_LEVEL", "MEDIUM").upper()
if THINKING_LEVEL not in ["LOW", "MEDIUM", "HIGH"]:
    THINKING_LEVEL = "MEDIUM"

# Model Configuration
MODEL_NAME = "gemini-3-pro-preview"

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL STATE
# ============================================================================

# HTTP session for connection pooling
http_session: requests.Session | None = None

# Gemini client
client: genai.Client | None = None

# Application start time
app_start_time: datetime | None = None

# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    global http_session, client, app_start_time
    
    # Startup
    logger.info("Starting Gemini 3.0 Pro API Server...")
    app_start_time = datetime.now()
    
    # Initialize HTTP session with connection pooling
    http_session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=3
    )
    http_session.mount("http://", adapter)
    http_session.mount("https://", adapter)
    logger.info("HTTP session initialized with connection pooling")
    
    # Initialize Gemini client
    client = genai.Client(api_key=API_KEY)
    logger.info(f"Gemini client initialized with model: {MODEL_NAME}")
    logger.info(f"Thinking mode: {'ENABLED' if THINKING_ENABLED else 'DISABLED'} (Level: {THINKING_LEVEL if THINKING_ENABLED else 'LOW'})")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Gemini 3.0 Pro API Server...")
    if http_session:
        http_session.close()
        logger.info("HTTP session closed")

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Gemini 3.0 Pro API Server",
    version="3.0.0",
    description="API server for Gemini 3.0 Pro with thinking capabilities",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================

class GenerateRequest(BaseModel):
    """Request model for /generate endpoint."""
    prompt: str = Field(..., description="User's prompt")
    json_schema: dict | None = Field(default=None, description="Optional JSON schema for structured output")
    image_urls: list[str] | None = Field(default=None, description="List of image URLs to analyze")
    image_url: str | None = Field(default=None, description="Single image URL (backward compatibility)")


class GenerateResponse(BaseModel):
    """Response model for /generate endpoint."""
    output: Union[dict, list, str]
    input_tokens: int
    output_tokens: int
    total_tokens: int


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: str = Field(..., description="Health status: 'healthy' or 'unhealthy'")
    timestamp: str = Field(..., description="Current server timestamp")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    model: str = Field(..., description="Model name")
    thinking_enabled: bool = Field(..., description="Whether thinking mode is enabled")
    thinking_level: str = Field(..., description="Thinking level configuration")
    version: str = Field(..., description="API version")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

@lru_cache(maxsize=1)
def load_system_prompt() -> str:
    """Load system instruction from system-instructions.md file.
    Cached to avoid repeated file reads.
    
    Returns:
        str: System instruction content
        
    Raises:
        RuntimeError: If system instruction file not found
    """
    prompt_file = os.path.join(os.path.dirname(__file__), "system-instructions.md")
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(
            f"System instruction file not found: {prompt_file}. "
            "Please create system-instructions.md in the same directory as main.py"
        )


def build_thinking_config() -> dict:
    """Build thinking config for Gemini 3.0 Pro.
    
    Returns:
        dict: Configuration with thinkingLevel (LOW, MEDIUM, or HIGH)
    """
    return {"thinkingLevel": THINKING_LEVEL if THINKING_ENABLED else "LOW"}


def convert_dict_to_schema(schema_dict: dict) -> types.Schema:
    """Convert a dictionary JSON schema to genai.types.Schema format.
    
    This follows the official Gemini API schema format using genai.types.Schema
    and genai.types.Type instead of plain dictionaries.
    
    Args:
        schema_dict: Dictionary representation of JSON schema
        
    Returns:
        types.Schema: Properly formatted Schema object
    """
    # Map JSON schema types to genai.types.Type
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


def load_image_from_url(url: str) -> tuple[bytes, str]:
    """Download image from URL and return bytes with MIME type.
    
    Uses global HTTP session for connection pooling.
    
    Args:
        url: Image URL to download
        
    Returns:
        tuple: (image_bytes, mime_type)
        
    Raises:
        HTTPException: If image download fails
    """
    try:
        response = http_session.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch image from {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {e}")

    # Determine MIME type
    content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
    mime_type = content_type if content_type.startswith("image/") else None

    if not mime_type:
        guessed, _ = mimetypes.guess_type(url)
        mime_type = guessed if guessed and guessed.startswith("image/") else "image/jpeg"

    return response.content, mime_type


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

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint to verify API is running.
    
    Returns:
        HealthResponse: Current health status and system information
    """
    try:
        uptime = (datetime.now() - app_start_time).total_seconds() if app_start_time else 0
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            uptime_seconds=uptime,
            model=MODEL_NAME,
            thinking_enabled=THINKING_ENABLED,
            thinking_level=THINKING_LEVEL if THINKING_ENABLED else "LOW",
            version="3.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.post("/generate", response_model=GenerateResponse, tags=["Generation"])
def generate(req: GenerateRequest):
    """Generate response from Gemini 3.0 Pro model.
    
    Args:
        req: GenerateRequest with prompt, optional images, and optional JSON schema
        
    Returns:
        GenerateResponse: Output with token usage statistics
        
    Raises:
        HTTPException: If generation fails or response is invalid
    """
    try:
        # Load system prompt
        system_prompt = load_system_prompt()
        
        parts: list[types.Part] = []

        # Collect all image URLs (supports both new and legacy formats)
        image_urls_to_process = []
        if req.image_urls:
            image_urls_to_process.extend(req.image_urls)
        if req.image_url:  # Backward compatibility
            image_urls_to_process.append(req.image_url)
        
        # Load and add all images as Parts
        for img_url in image_urls_to_process:
            img_bytes, mime_type = load_image_from_url(img_url)
            parts.append(types.Part.from_bytes(mime_type=mime_type, data=img_bytes))
            logger.info(f"Loaded image from {img_url} (type: {mime_type})")

        # Add user prompt
        parts.append(types.Part.from_text(text=req.prompt))

        # Build request
        contents = [types.Content(role="user", parts=parts)]
        
        # Build config
        config_params = {
            "system_instruction": [types.Part.from_text(text=system_prompt)],
            "temperature": 0.6,
            "top_p": 0.4,
            "max_output_tokens": 12000,
            "thinkingConfig": build_thinking_config(),
            "media_resolution": "MEDIA_RESOLUTION_MEDIUM",
        }
        
        # If JSON schema provided, enforce structured JSON output
        if req.json_schema:
            config_params["response_mime_type"] = "application/json"
            config_params["response_schema"] = convert_dict_to_schema(req.json_schema)
        
        config = types.GenerateContentConfig(**config_params)

        # Generate content
        logger.info(f"Generating content with model: {MODEL_NAME}")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=config,
        )

        # Parse response - try JSON first, fallback to raw text
        try:
            parsed_output = json.loads(response.text)
        except json.JSONDecodeError:
            # Not JSON, return as-is (could be markdown, text, etc.)
            parsed_output = response.text

        # Extract token usage
        input_tokens, output_tokens, total_tokens = extract_token_counts(
            getattr(response, "usage_metadata", None)
        )

        # Log usage
        has_schema = "with_schema" if req.json_schema else "natural"
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


# ============================================================================
# CUSTOM EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom handler for HTTP exceptions with logging."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Custom handler for unexpected exceptions with logging."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

# uvicorn main:app --host 0.0.0.0 --port 8000
#
# Health check:
# curl http://localhost:8000/health
#
# With JSON schema (structured output):
# {
#   "prompt": "Extract pricing tiers",
#   "json_schema": {
#     "type": "object",
#     "required": ["tiers"],
#     "properties": {
#       "tiers": {
#         "type": "array",
#         "items": {
#           "type": "object",
#           "properties": {
#             "name": {"type": "string"},
#             "price": {"type": "number"}
#           }
#         }
#       }
#     }
#   }
# }
#
# Without schema (AI decides format):
# {
#   "prompt": "Write a review of this landing page",
#   "image_urls": ["https://example.com/screenshot.png"]
# }