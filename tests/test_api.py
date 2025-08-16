import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Phishing URL Detection API"

def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "api_version" in data

def test_status():
    """Test status endpoint"""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "loaded" in data
    assert "total_predictions" in data

def test_check_url_without_model():
    """Test URL check when model is not loaded"""
    response = client.post(
        "/check-url",
        json={"url": "https://www.google.com"}
    )
    # Should return service unavailable if no model is loaded
    assert response.status_code in [200, 503]

def test_check_url_invalid_format():
    """Test URL check with invalid URL format"""
    response = client.post(
        "/check-url",
        json={"url": "not-a-valid-url"}
    )
    assert response.status_code == 422  # Validation error

def test_check_url_empty():
    """Test URL check with empty URL"""
    response = client.post(
        "/check-url",
        json={"url": ""}
    )
    assert response.status_code == 422  # Validation error

def test_batch_urls_empty_list():
    """Test batch URL check with empty list"""
    response = client.post(
        "/check-urls-batch",
        json={"urls": []}
    )
    assert response.status_code == 422  # Validation error

def test_batch_urls_too_many():
    """Test batch URL check with too many URLs"""
    urls = ["https://example.com"] * 101  # Exceed limit of 100
    response = client.post(
        "/check-urls-batch",
        json={"urls": urls}
    )
    assert response.status_code == 422  # Validation error

def test_get_features_endpoint():
    """Test feature extraction endpoint"""
    response = client.get("/features/https://www.example.com")
    # Should return 200 if feature extractor is initialized
    assert response.status_code in [200, 503]

if __name__ == "__main__":
    pytest.main([__file__])
