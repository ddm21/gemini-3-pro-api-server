"""
Shared dependencies and lifespan management.

Manages global resources like HTTP session, Gemini client, and application lifecycle.
"""

from contextlib import asynccontextmanager
from datetime import datetime
import logging

import requests
from fastapi import FastAPI
from google import genai

from app.config import API_KEY, MODEL_NAME

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
    logger.info("Thinking mode: ENABLED by default (Gemini 3.0 Pro) - Level configurable per request")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Gemini 3.0 Pro API Server...")
    if http_session:
        http_session.close()
        logger.info("HTTP session closed")


# ============================================================================
# DEPENDENCY GETTERS
# ============================================================================

def get_http_session() -> requests.Session:
    """Get the global HTTP session."""
    if http_session is None:
        raise RuntimeError("HTTP session not initialized")
    return http_session


def get_gemini_client() -> genai.Client:
    """Get the global Gemini client."""
    if client is None:
        raise RuntimeError("Gemini client not initialized")
    return client


def get_app_start_time() -> datetime:
    """Get the application start time."""
    if app_start_time is None:
        raise RuntimeError("Application start time not set")
    return app_start_time
