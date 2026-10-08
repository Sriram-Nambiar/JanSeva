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
