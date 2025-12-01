"""Integration tests for API endpoints."""

import pytest


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "app" in data
        assert "docs" in data


class TestSessionsAPI:
    """Tests for sessions API endpoints."""

    def test_list_sessions_empty(self, client):
        response = client.get("/api/v1/sessions")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 0
        assert data["sessions"] == []

    def test_list_years_empty(self, client):
        response = client.get("/api/v1/sessions/years")
        assert response.status_code == 200

        data = response.json()
        assert "years" in data

    def test_get_session_not_found(self, client):
        response = client.get("/api/v1/sessions/id/nonexistent")
        assert response.status_code == 404

    def test_get_event_sessions_not_found(self, client):
        response = client.get("/api/v1/sessions/2024/1")
        assert response.status_code == 404


class TestLapsAPI:
    """Tests for laps API endpoints."""

    def test_get_laps_session_not_found(self, client):
        response = client.get("/api/v1/laps/nonexistent")
        assert response.status_code == 404

    def test_get_fastest_laps_empty(self, client):
        # This will return empty since session doesn't exist
        response = client.get("/api/v1/laps/2024_01_R/fastest")
        # The endpoint returns empty list, not 404
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0


class TestStrategyAPI:
    """Tests for strategy API endpoints."""

    def test_get_stints_empty(self, client):
        response = client.get("/api/v1/strategy/2024_01_R/stints")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 0

    def test_get_strategy_summary_empty(self, client):
        response = client.get("/api/v1/strategy/2024_01_R/summary")
        assert response.status_code == 200

        data = response.json()
        assert data["strategies"] == []


class TestIngestionAPI:
    """Tests for ingestion API endpoints."""

    def test_check_ingestion_status(self, client):
        response = client.get("/api/v1/ingest/status/2024/1/R")
        assert response.status_code == 200

        data = response.json()
        assert data["year"] == 2024
        assert data["round_number"] == 1
        assert data["session_type"] == "R"
        assert data["is_ingested"] is False
