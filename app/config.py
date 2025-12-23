"""
Configuration module for Gemini 3.0 Pro API Server.

Contains all environment variables and configuration constants.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY not set in env or .env")

# Validate API key format
if not API_KEY.startswith("AIza") or len(API_KEY) < 30:
    logger.warning("API key format may be invalid")

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# Server API key for authenticating requests to this server
SERVER_API_KEY = os.getenv("SERVER_API_KEY")
if not SERVER_API_KEY:
    logger.warning("SERVER_API_KEY not set - API will be unauthenticated!")

# CORS allowed origins (comma-separated)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
if not ALLOWED_ORIGINS:
    logger.warning("ALLOWED_ORIGINS not set - CORS will block all origins")

# Rate limiting
RATE_LIMIT = os.getenv("RATE_LIMIT", "10/minute")

# Request timeouts
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

MODEL_NAME = "gemini-3-pro-preview"

# Supported models
SUPPORTED_MODELS = [
    "gemini-3-pro-preview",
    "gemini-3-flash-preview"
]

# Model-specific thinking levels
THINKING_LEVELS = {
    "gemini-3-pro-preview": ["LOW", "HIGH"],
    "gemini-3-flash-preview": ["minimal", "low", "medium", "high"]
}

# ============================================================================
# FILE SIZE LIMITS
# ============================================================================

MAX_PROMPT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = 20 * 1024 * 1024   # 20MB

# ============================================================================
# GENERATION DEFAULTS
# ============================================================================

DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "1.0"))
DEFAULT_TOP_P = float(os.getenv("DEFAULT_TOP_P", "0.95"))
DEFAULT_MAX_OUTPUT_TOKENS = int(os.getenv("DEFAULT_MAX_OUTPUT_TOKENS", "12000"))

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)
