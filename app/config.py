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

# ============================================================================
# THINKING CONFIGURATION
# ============================================================================

THINKING_ENABLED = os.getenv("THINKING_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
THINKING_LEVEL = os.getenv("THINKING_LEVEL", "MEDIUM").upper()
if THINKING_LEVEL not in ["LOW", "MEDIUM", "HIGH"]:
    THINKING_LEVEL = "MEDIUM"

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

MODEL_NAME = "gemini-3-pro-preview"

# ============================================================================
# FILE SIZE LIMITS
# ============================================================================

MAX_PROMPT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = 20 * 1024 * 1024   # 20MB

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)
