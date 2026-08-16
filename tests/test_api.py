import pytest
from fastapi.testclient import TestClient
from app.main import app
import app.api.agent as agent

client = TestClient(app)

def test_health_endpoint():
    """W11 Integration Test: Health Check Endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_run_agent_missing_auth():
    """W11 Security Test: API Key Verification Missing"""
    payload = {
        "user_id": "test_user",
        "pesan": "halo",
        "webhook_url": "http://localhost/webhook"
    }
    response = client.post("/api/v1/run-agent", json=payload)
    assert response.status_code == 401
    assert "Missing" in response.json()["detail"] or "missing" in response.json()["detail"]

def test_run_agent_valid_auth(monkeypatch):
    """W11 Integration Test: Valid Background Task Execution Flow"""
    # Mock token value during test environment matching API behavior
    monkeypatch.setattr(agent.settings, "API_KEY", "test_key")
    
    # Bypass Graph execution to avoid Postgres Connection in isolated test environment
    async def mock_create_agent_graph():
        class MockApp:
            async def ainvoke(self, state, config):
                return {"status": "success", "final_answer": "Mock Answer"}
        return MockApp()
    monkeypatch.setattr(agent, "create_agent_graph", mock_create_agent_graph)
    
    payload = {
        "user_id": "test_user_01",
        "pesan": "cek total penjualan",
        "webhook_url": "http://localhost/webhook"
    }
    headers = {"Authorization": "Bearer test_key"}
    
    response = client.post("/api/v1/run-agent", headers=headers, json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "processing"
