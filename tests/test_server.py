<<<<<<< HEAD
"""Tests for JanSeva 2.0 FastAPI Server and Gemma Harness integration."""

import os
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from server import app
from core.gemma_harness import (
    GemmaHarness,
    LMStudioConnectionError,
    ModelNotConfiguredError,
    LMStudioAPIError,
    build_janseva_prompt,
)

client = TestClient(app)


def test_read_root():
    """Test GET / endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["application"] == "JanSeva"
    assert data["version"] == "2.0"
    assert data["status"] == "running"


def test_health_check():
    """Test GET /health and GET /api/health endpoints."""
    res1 = client.get("/health")
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["status"] == "online"
    assert d1["application"] == "JanSeva"
    assert "mock_ai" in d1

    res2 = client.get("/api/health")
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["status"] == "online"


def test_chat_mock_mode(monkeypatch):
    """Test POST /api/chat in default mock mode."""
    monkeypatch.setenv("JANSEVA_MOCK_AI", "true")

    response = client.post(
        "/api/chat",
        json={"prompt": "Explain why this welfare application may be rejected."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert "Mock JanSeva AI response" in data["response"]


def test_chat_missing_prompt():
    """Test POST /api/chat with missing prompt field."""
    response = client.post("/api/chat", json={})
    assert response.status_code == 422


def test_chat_empty_prompt():
    """Test POST /api/chat with whitespace-only prompt."""
    response = client.post("/api/chat", json={"prompt": "   "})
    assert response.status_code == 422


def test_chat_real_mode_success(monkeypatch):
    """Test POST /api/chat in real mode when LM Studio returns valid output."""
    monkeypatch.setenv("JANSEVA_MOCK_AI", "false")
    monkeypatch.setenv("GEMMA_MODEL_ID", "gemma-4-2b")

    with patch.object(
        GemmaHarness,
        "send_chat_request",
        return_value="Analysis: Ration card name does not match Aadhaar.",
    ):
        response = client.post(
            "/api/chat",
            json={"prompt": "Check my documents."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "lm-studio"
        assert data["response"] == "Analysis: Ration card name does not match Aadhaar."


def test_chat_real_mode_connection_error(monkeypatch):
    """Test POST /api/chat error handling when LM Studio is offline."""
    monkeypatch.setenv("JANSEVA_MOCK_AI", "false")

    with patch.object(
        GemmaHarness,
        "send_chat_request",
        side_effect=LMStudioConnectionError("LM Studio is not running or unreachable at http://localhost:1234."),
    ):
        response = client.post(
            "/api/chat",
            json={"prompt": "Check documents."},
        )
        assert response.status_code == 503
        data = response.json()
        assert "LM Studio is not running" in data["detail"]


def test_chat_real_mode_model_not_configured(monkeypatch):
    """Test POST /api/chat error handling when model ID is missing."""
    monkeypatch.setenv("JANSEVA_MOCK_AI", "false")

    with patch.object(
        GemmaHarness,
        "send_chat_request",
        side_effect=ModelNotConfiguredError("GEMMA_MODEL_ID is not configured."),
    ):
        response = client.post(
            "/api/chat",
            json={"prompt": "Check documents."},
        )
        assert response.status_code == 400
        data = response.json()
        assert "GEMMA_MODEL_ID is not configured" in data["detail"]


def test_get_models_success():
    """Test GET /api/models returning available models."""
    mock_models = [{"id": "gemma-4-2b-it", "object": "model"}]
    with patch.object(GemmaHarness, "get_available_models", return_value=mock_models):
        response = client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["models"] == mock_models


def test_get_models_connection_error():
    """Test GET /api/models when LM Studio is unreachable."""
    with patch.object(
        GemmaHarness,
        "get_available_models",
        side_effect=LMStudioConnectionError("LM Studio is unreachable"),
    ):
        response = client.get("/api/models")
        assert response.status_code == 503
        data = response.json()
        assert "LM Studio is unreachable" in data["detail"]


def test_build_janseva_prompt():
    """Test prompt helper formatting."""
    prompt = build_janseva_prompt("Name: Ramesh vs Ramu")
    assert "You are JanSeva's welfare preflight assistant." in prompt
    assert "Rules decide. AI explains. Humans verify." in prompt
    assert "Name: Ramesh vs Ramu" in prompt
=======
"""Unit tests for FastAPI endpoints including openZIM scraper and download."""

import pytest
from fastapi.testclient import TestClient
from server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "JanSeva" in data["app"]


def test_list_scraped_packs(client):
    response = client.get("/api/scraped-packs")
    assert response.status_code == 200
    data = response.json()
    assert "packs" in data
    assert isinstance(data["packs"], list)
    # Check that packs has at least 1 item since we built welfare_curated.zim
    assert len(data["packs"]) >= 1
    sample = data["packs"][0]
    assert "filename" in sample
    assert "filesize_kb" in sample


def test_download_zim_endpoint(client):
    # Test downloading one of the existing packs
    packs_resp = client.get("/api/scraped-packs")
    packs = packs_resp.json()["packs"]
    if packs:
        first_pack = packs[0]["filename"]
        download_resp = client.get(f"/api/download-zim/{first_pack}")
        assert download_resp.status_code == 200
        assert len(download_resp.content) > 1000


def test_inspect_zim_endpoint(client):
    packs_resp = client.get("/api/scraped-packs")
    packs = packs_resp.json()["packs"]
    if packs:
        first_pack = packs[0]["filename"]
        inspect_resp = client.get(f"/api/inspect-zim/{first_pack}")
        assert inspect_resp.status_code == 200
        data = inspect_resp.json()
        assert data["filename"] == first_pack
        assert "metadata" in data


def test_trigger_scrape_curated(client):
    payload = {
        "output_name": "test_api_pack.zim",
        "title": "API Generated Pack",
        "curated_pack": True,
        "language": "eng",
    }
    response = client.post("/api/scrape-to-zim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"] == "test_api_pack.zim"
    assert data["filesize_kb"] > 10
>>>>>>> origin/main
