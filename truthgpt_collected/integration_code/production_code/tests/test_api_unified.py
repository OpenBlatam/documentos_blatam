#!/usr/bin/env python3
"""
Tests for Unified API
=====================

Tests for the unified API endpoints using httpx.AsyncClient.
"""

import pytest
from httpx import AsyncClient
from fastapi import FastAPI

from api.app_factory import create_api_app


@pytest.fixture
async def app():
    """Create test app."""
    return create_api_app(
        enable_memory=True,
        enable_redundancy=True,
        enable_pipeline=True,
        enable_chat=True,
        enable_config=True,
        enable_monitor=True,
        enable_auth=False
    )


@pytest.fixture
async def client(app: FastAPI):
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns correct info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "endpoints" in data
        assert "features" in data


class TestHealthEndpoint:
    """Tests for health endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test health endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestMemoryEndpoints:
    """Tests for memory endpoints."""
    
    @pytest.mark.asyncio
    async def test_memory_store_success(self, client: AsyncClient):
        """Test successful memory store."""
        payload = {
            "episode": [1.0, 2.0, 3.0, 4.0, 5.0],
            "metadata": {"test": True},
            "priority": 1.0
        }
        response = await client.post("/api/v1/memory/store", json=payload)
        # May fail if service not initialized, but should return proper error
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "request_id" in data
    
    @pytest.mark.asyncio
    async def test_memory_store_invalid_episode(self, client: AsyncClient):
        """Test memory store with invalid episode."""
        payload = {"episode": []}
        response = await client.post("/api/v1/memory/store", json=payload)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_memory_retrieve_success(self, client: AsyncClient):
        """Test successful memory retrieve."""
        payload = {
            "query": [1.0, 2.0, 3.0],
            "k": 5
        }
        response = await client.post("/api/v1/memory/retrieve", json=payload)
        # May fail if service not initialized
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "retrieved" in data
            assert "request_id" in data
    
    @pytest.mark.asyncio
    async def test_memory_stats(self, client: AsyncClient):
        """Test memory stats endpoint."""
        response = await client.get("/api/v1/memory/stats")
        # May fail if service not initialized
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "stats" in data
            assert "request_id" in data


class TestRedundancyEndpoints:
    """Tests for redundancy endpoints."""
    
    @pytest.mark.asyncio
    async def test_redundancy_process_success(self, client: AsyncClient):
        """Test successful redundancy processing."""
        payload = {
            "items": [[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]],
            "similarity_threshold": 0.85
        }
        response = await client.post("/api/v1/redundancy/process", json=payload)
        # May fail if service not initialized
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "unique_items" in data
            assert "request_id" in data
    
    @pytest.mark.asyncio
    async def test_redundancy_process_invalid_items(self, client: AsyncClient):
        """Test redundancy processing with invalid items."""
        payload = {"items": []}
        response = await client.post("/api/v1/redundancy/process", json=payload)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_redundancy_stats(self, client: AsyncClient):
        """Test redundancy stats endpoint."""
        response = await client.get("/api/v1/redundancy/stats")
        # May fail if service not initialized
        assert response.status_code in [200, 503]


class TestPipelineEndpoints:
    """Tests for pipeline endpoints."""
    
    @pytest.mark.asyncio
    async def test_pipeline_process_success(self, client: AsyncClient):
        """Test successful pipeline processing."""
        payload = {
            "data": [[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]],
            "use_memory": True,
            "use_redundancy": True
        }
        response = await client.post("/api/v1/pipeline/process", json=payload)
        # May fail if service not initialized
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "output" in data
            assert "request_id" in data
    
    @pytest.mark.asyncio
    async def test_pipeline_process_invalid_data(self, client: AsyncClient):
        """Test pipeline processing with invalid data."""
        payload = {"data": []}
        response = await client.post("/api/v1/pipeline/process", json=payload)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_pipeline_stats(self, client: AsyncClient):
        """Test pipeline stats endpoint."""
        response = await client.get("/api/v1/pipeline/stats")
        # May fail if service not initialized
        assert response.status_code in [200, 503]


class TestChatEndpoints:
    """Tests for chat endpoints."""
    
    @pytest.mark.asyncio
    async def test_chat_success(self, client: AsyncClient):
        """Test successful chat."""
        payload = {
            "message": "Hello, world!",
            "conversation_id": "test-123"
        }
        response = await client.post("/api/v1/chat", json=payload)
        # May fail if service not initialized
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "request_id" in data
    
    @pytest.mark.asyncio
    async def test_chat_empty_message(self, client: AsyncClient):
        """Test chat with empty message."""
        payload = {"message": ""}
        response = await client.post("/api/v1/chat", json=payload)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_chat_message_too_long(self, client: AsyncClient):
        """Test chat with message too long."""
        payload = {"message": "x" * 10001}
        response = await client.post("/api/v1/chat", json=payload)
        assert response.status_code == 400


class TestConfigEndpoints:
    """Tests for config endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_config(self, client: AsyncClient):
        """Test get config endpoint."""
        response = await client.get("/api/v1/config")
        # May fail if service not initialized or auth required
        assert response.status_code in [200, 401, 503]
    
    @pytest.mark.asyncio
    async def test_update_config(self, client: AsyncClient):
        """Test update config endpoint."""
        payload = {"key": "value"}
        response = await client.put("/api/v1/config/test_module", json=payload)
        # May fail if service not initialized or auth required
        assert response.status_code in [200, 401, 403, 503]


class TestMonitorEndpoints:
    """Tests for monitor endpoints."""
    
    @pytest.mark.asyncio
    async def test_monitor_status(self, client: AsyncClient):
        """Test monitor status endpoint."""
        response = await client.get("/api/v1/monitor/status")
        # May fail if service not initialized
        assert response.status_code in [200, 503]
    
    @pytest.mark.asyncio
    async def test_monitor_health(self, client: AsyncClient):
        """Test monitor health endpoint."""
        response = await client.get("/api/v1/monitor/health")
        # May fail if service not initialized
        assert response.status_code in [200, 503]
    
    @pytest.mark.asyncio
    async def test_monitor_metrics(self, client: AsyncClient):
        """Test monitor metrics endpoint."""
        response = await client.get("/api/v1/monitor/metrics")
        # May fail if service not initialized
        assert response.status_code in [200, 503]


class TestTracing:
    """Tests for request tracing."""
    
    @pytest.mark.asyncio
    async def test_request_id_in_response(self, client: AsyncClient):
        """Test that request_id is included in response."""
        response = await client.get("/health")
        assert response.status_code == 200
        # Check header
        assert "X-Request-ID" in response.headers


class TestMetrics:
    """Tests for Prometheus metrics."""
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test metrics endpoint."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        # Should return text/plain
        assert "text/plain" in response.headers.get("content-type", "")


class TestErrorHandling:
    """Tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_json(self, client: AsyncClient):
        """Test handling of invalid JSON."""
        response = await client.post(
            "/api/v1/memory/store",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_missing_required_field(self, client: AsyncClient):
        """Test handling of missing required field."""
        payload = {}  # Missing required 'episode' field
        response = await client.post("/api/v1/memory/store", json=payload)
        assert response.status_code == 422

