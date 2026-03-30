"""Tests for the Meta-LLM-Selector web API."""

from __future__ import annotations

import json
import os
import sys
import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from web.app import app


@pytest.fixture
def client():
    return TestClient(app)


# ═══════════════════════════════════════════════
# Static File / Health Tests
# ═══════════════════════════════════════════════


class TestHealth:
    """Health and static file endpoints."""

    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "gemini_configured" in data
        assert "exa_configured" in data

    def test_root_serves_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Meta-LLM Selector" in resp.text

    def test_static_css(self, client):
        resp = client.get("/static/style.css")
        assert resp.status_code == 200
        assert "text/css" in resp.headers["content-type"]

    def test_static_js(self, client):
        resp = client.get("/static/app.js")
        assert resp.status_code == 200
        assert "javascript" in resp.headers["content-type"]

    def test_static_404(self, client):
        resp = client.get("/static/nonexistent.xyz")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════
# Analyze Endpoint Tests (structure only — no real LLM call)
# ═══════════════════════════════════════════════


class TestAnalyzeEndpoint:
    """Tests for the /api/analyze SSE streaming endpoint."""

    def test_analyze_returns_sse_stream(self, client):
        """POST should return a text/event-stream response."""
        resp = client.post(
            "/api/analyze",
            json={"prompt": "test only - do not run real pipeline"},
            timeout=10,
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    def test_analyze_requires_prompt(self, client):
        """POST without prompt should fail validation."""
        resp = client.post("/api/analyze", json={})
        assert resp.status_code == 422  # Pydantic validation error

    def test_analyze_rejects_get(self, client):
        """GET on /api/analyze should be 405."""
        resp = client.get("/api/analyze")
        assert resp.status_code == 405

    def test_sse_stream_has_data_lines(self, client):
        """The SSE response should contain data: lines."""
        resp = client.post(
            "/api/analyze",
            json={"prompt": "budget coding assistant"},
            timeout=120,
        )
        # The response body should contain at least one SSE data line
        lines = resp.text.strip().split("\n")
        data_lines = [l for l in lines if l.startswith("data: ")]
        assert len(data_lines) > 0, "Expected at least one SSE data line"

        # Each data line should be valid JSON
        for dl in data_lines:
            payload = json.loads(dl[6:])  # strip "data: "
            assert "type" in payload
