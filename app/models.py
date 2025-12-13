"""
Pydantic models for request and response validation.
"""

from typing import Union
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request model for /generate endpoint (JSON)."""
    user_prompt: str = Field(..., description="User's prompt (text or file URL)")
    user_prompt_type: str = Field("text", description="Type of user_prompt: 'text' or 'file'")
    system_prompt: str | None = Field(None, description="System instruction (text or file URL)")
    system_prompt_type: str = Field("text", description="Type of system_prompt: 'text' or 'file'")
    image_urls: list[str] | None = Field(None, description="List of image URLs")
    json_schema: dict | None = Field(None, description="JSON schema for structured output")
    thinking_level: str = Field("HIGH", description="Thinking level: 'LOW' or 'HIGH'")
    media_resolution: str = Field("MEDIUM", description="Media resolution: 'LOW', 'MEDIUM', or 'HIGH'")


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
    version: str = Field(..., description="API version")
