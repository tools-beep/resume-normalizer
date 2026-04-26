from tests.conftest import TEST_ADMIN_KEY


def test_create_key(client):
    """Admin can create a new API key."""
    response = client.post(
        "/api/v1/keys",
        json={"name": "my-app"},
        headers={"X-Admin-Key": TEST_ADMIN_KEY},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["key"].startswith("rn_live_")
    assert data["key_info"]["name"] == "my-app"
    assert data["key_info"]["is_active"] is True


def test_create_key_no_admin(client):
    """Requests without admin key return 401."""
    response = client.post("/api/v1/keys", json={"name": "my-app"})
    assert response.status_code == 401


def test_create_key_wrong_admin(client):
    """Wrong admin key returns 403."""
    response = client.post(
        "/api/v1/keys",
        json={"name": "my-app"},
        headers={"X-Admin-Key": "wrong-key"},
    )
    assert response.status_code == 403


def test_list_keys(client):
    """Admin can list all keys."""
    # Create a key first
    client.post(
        "/api/v1/keys",
        json={"name": "list-test"},
        headers={"X-Admin-Key": TEST_ADMIN_KEY},
    )

    response = client.get(
        "/api/v1/keys",
        headers={"X-Admin-Key": TEST_ADMIN_KEY},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_revoke_key(client):
    """Admin can revoke a key."""
    # Create a key
    create_resp = client.post(
        "/api/v1/keys",
        json={"name": "revoke-test"},
        headers={"X-Admin-Key": TEST_ADMIN_KEY},
    )
    key_id = create_resp.json()["key_info"]["id"]

    # Revoke it
    response = client.delete(
        f"/api/v1/keys/{key_id}",
        headers={"X-Admin-Key": TEST_ADMIN_KEY},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "revoked"


def test_revoke_nonexistent_key(client):
    """Revoking a nonexistent key returns 404."""
    response = client.delete(
        "/api/v1/keys/99999",
        headers={"X-Admin-Key": TEST_ADMIN_KEY},
    )
    assert response.status_code == 404
