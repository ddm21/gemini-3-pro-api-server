"""
Test fixtures and configuration.
"""

import os
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Set test environment variables before importing app
os.environ["GEMINI_API_KEY"] = "AIzatest-key-for-testing-purposes-only-1234567890"
os.environ["SERVER_API_KEY"] = "test-server-api-key-12345"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://testorigin.com"
os.environ["RATE_LIMIT"] = "100/minute"  # Higher limit for tests

from main import app
import app.dependencies as deps


@pytest.fixture(autouse=True)
def setup_app_state():
    """Setup app state for tests."""
    # Initialize app_start_time for health check
    deps.app_start_time = datetime.now()
    yield
    # Cleanup if needed


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def valid_api_key():
    """Return valid API key for testing."""
    return "test-server-api-key-12345"


@pytest.fixture
def invalid_api_key():
    """Return invalid API key for testing."""
    return "invalid-api-key"


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client for testing."""
    with patch('app.dependencies.client') as mock_client:
        # Mock successful response
        mock_response = Mock()
        mock_response.text = '{"result": "test output"}'
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20
        mock_response.usage_metadata.total_token_count = 30
        
        mock_client.models.generate_content.return_value = mock_response
        yield mock_client


@pytest.fixture
def sample_generate_request():
    """Sample valid generate request."""
    return {
        "user_prompt": "Hello, world!",
        "user_prompt_type": "text",
        "thinking_level": "HIGH",
        "media_resolution": "MEDIUM"
    }
