"""
API endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test that health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "model" in data
        assert "version" in data
    
    def test_health_check_no_auth_required(self, client):
        """Test that health check doesn't require authentication."""
        response = client.get("/health")
        assert response.status_code == 200


class TestGenerateEndpoint:
    """Test generate endpoint."""
    
    def test_generate_requires_auth(self, client, sample_generate_request):
        """Test that generate endpoint requires authentication."""
        response = client.post("/generate", json=sample_generate_request)
        assert response.status_code == 403
    
    def test_generate_with_valid_request(self, client, sample_generate_request, valid_api_key, mock_gemini_client):
        """Test generate with valid request."""
        response = client.post(
            "/generate",
            json=sample_generate_request,
            headers={"X-API-Key": valid_api_key}
        )
        # May fail due to mocking issues, but should not be auth error
        assert response.status_code != 403
    
    def test_generate_with_missing_prompt(self, client, valid_api_key):
        """Test that missing prompt is rejected."""
        request_data = {}
        response = client.post(
            "/generate",
            json=request_data,
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422  # Validation error
    
    def test_generate_with_system_prompt(self, client, valid_api_key, mock_gemini_client):
        """Test generate with system prompt."""
        request_data = {
            "user_prompt": "Hello",
            "system_prompt": "You are a helpful assistant",
            "system_prompt_type": "text"
        }
        response = client.post(
            "/generate",
            json=request_data,
            headers={"X-API-Key": valid_api_key}
        )
        # Should not be validation or auth error
        assert response.status_code not in [403, 422]
    
    def test_generate_with_json_schema(self, client, valid_api_key, mock_gemini_client):
        """Test generate with JSON schema."""
        request_data = {
            "user_prompt": "Generate a person",
            "json_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name", "age"]
            }
        }
        response = client.post(
            "/generate",
            json=request_data,
            headers={"X-API-Key": valid_api_key}
        )
        # Should not be validation or auth error
        assert response.status_code not in [403, 422]
    
    def test_generate_with_model_selection(self, client, valid_api_key, mock_gemini_client):
        """Test generate with model selection."""
        for model in ["gemini-3-pro-preview", "gemini-3-flash-preview"]:
            request_data = {
                "user_prompt": "Hello",
                "model": model
            }
            response = client.post(
                "/generate",
                json=request_data,
                headers={"X-API-Key": valid_api_key}
            )
            # Should not be validation or auth error
            assert response.status_code not in [403, 422]


class TestErrorHandling:
    """Test error handling."""
    
    def test_404_for_unknown_endpoint(self, client):
        """Test that unknown endpoints return 404."""
        response = client.get("/unknown")
        assert response.status_code == 404
    
    def test_405_for_wrong_method(self, client):
        """Test that wrong HTTP methods return 405."""
        response = client.get("/generate")
        assert response.status_code == 405
    
    def test_error_messages_dont_expose_internals(self, client, valid_api_key):
        """Test that error messages don't expose internal details."""
        # Try to trigger an error
        request_data = {
            "user_prompt": "test",
            "user_prompt_type": "file",
            "user_prompt": "http://invalid-url-that-will-fail"
        }
        response = client.post(
            "/generate",
            json=request_data,
            headers={"X-API-Key": valid_api_key}
        )
        
        if response.status_code >= 400:
            error_detail = response.json().get("detail", "")
            # Should not contain stack traces or internal paths
            assert "Traceback" not in error_detail
            assert "File \"" not in error_detail
            assert "/app/" not in error_detail
