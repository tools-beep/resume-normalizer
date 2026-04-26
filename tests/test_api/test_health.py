from unittest.mock import MagicMock, patch


def test_health_endpoint(client):
    """Health endpoint returns 200 with correct structure."""
    with patch("app.api.routes.health.get_s3_service") as mock_s3_dep:
        mock_s3 = MagicMock()
        mock_s3.check_connectivity.return_value = True

        # Override the dependency at app level
        from app.dependencies import get_s3_service

        client.app.dependency_overrides[get_s3_service] = lambda: mock_s3

        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "services" in data

        client.app.dependency_overrides.pop(get_s3_service, None)
