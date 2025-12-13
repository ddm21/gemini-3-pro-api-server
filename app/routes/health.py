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
    """Health check endpoint to verify API is running."""
    try:
        app_start_time = get_app_start_time()
        uptime = (datetime.now() - app_start_time).total_seconds()
        
        return HealthResponse(
            status="healthy",
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
