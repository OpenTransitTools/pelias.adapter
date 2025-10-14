from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_read_root():
    """Test root endpoint"""
    response = client.get("core/v1/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_read_info():
    """Test info endpoint"""
    response = client.get("core/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data


def test_health_check():
    """Test health check endpoint"""
    response = client.get("core/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "message" in data
    assert data["message"] == "Service is healthy"
