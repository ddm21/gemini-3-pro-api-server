"""
Health check endpoint.

Provides server health status and configuration information.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from app.config import MODEL_NAME
from app.models import HealthResponse
from app.dependencies import get_app_start_time

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint to verify API is running and Gemini API is accessible."""
    try:
        app_start_time = get_app_start_time()
        uptime = (datetime.now() - app_start_time).total_seconds()
        
        # Test Gemini API connectivity
        api_status = "healthy"
        try:
            from app.dependencies import get_gemini_client
            client = get_gemini_client()
            # Lightweight test - just verify client is initialized
            # Actual API call would be too expensive for health check
            if client is None:
                api_status = "degraded"
                logger.warning("Gemini client not initialized")
        except Exception as e:
            api_status = "degraded"
            logger.warning(f"Gemini API connectivity issue: {e}")
        
        return HealthResponse(
            status=api_status,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=uptime,
            model=MODEL_NAME,
            version="3.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )
