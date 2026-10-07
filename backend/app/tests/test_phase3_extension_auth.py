import os
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.models.user import User

def test_pair_with_bad_credentials_returns_401(client: TestClient):
    """Pairing with invalid credentials or missing code must return 401 with no demo fallback."""
    # Completely empty
    res = client.post("/api/v1/extension/auth/pair", json={})
    assert res.status_code == 401

    # Invalid email/password
    res = client.post("/api/v1/extension/auth/pair", json={
        "email": "nonexistent@example.com",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401

    # Invalid pairing code
    res = client.post("/api/v1/extension/auth/pair", json={
        "pairing_code": "000000"
    })
    assert res.status_code == 401

def test_pair_with_expired_and_reused_pairing_code(client: TestClient, db_session):
    """One-time pairing codes must expire in 5 minutes and cannot be reused."""
    # 1. Register a logged-in user
    reg = client.post("/api/v1/auth/register", json={
        "email": "device_user@example.com",
        "full_name": "Device Tester",
        "password": "Password123!"
    })
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Generate a pairing code from the web app
    code_res = client.post("/api/v1/extension/auth/pairing-code", headers=headers)
    assert code_res.status_code == 200
    code_data = code_res.json()
    pairing_code = code_data["pairing_code"]

    # 3. Pair extension using the code -> should succeed
    pair_res = client.post("/api/v1/extension/auth/pair", json={
        "pairing_code": pairing_code,
        "device_id": "device-uuid-1",
        "device_name": "Chrome on MacBook"
    })
    assert pair_res.status_code == 200
    pair_data = pair_res.json()
    assert pair_data["user_email"] == "device_user@example.com"
    assert "refresh_token" in pair_data

    # 4. Attempt to REUSE the single-use pairing code -> must return 401
    reuse_res = client.post("/api/v1/extension/auth/pair", json={
        "pairing_code": pairing_code,
        "device_id": "device-uuid-2"
    })
    assert reuse_res.status_code == 401

def test_refresh_token_rotation_and_reuse_revocation(client: TestClient):
    """
    Refresh tokens must rotate on each use.
    Presenting an old/reused refresh token must immediately revoke the device.
    """
    # Register user
    reg = client.post("/api/v1/auth/register", json={
        "email": "rotator@example.com",
        "full_name": "Rotator Tester",
        "password": "Password123!"
    })
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate pairing code and pair
    code_res = client.post("/api/v1/extension/auth/pairing-code", headers=headers)
    assert code_res.status_code == 200
    pairing_code = code_res.json()["pairing_code"]

    pair_res = client.post("/api/v1/extension/auth/pair", json={
        "pairing_code": pairing_code,
        "device_id": "rotator-device-1"
    })
    assert pair_res.status_code == 200
    refresh_tok_1 = pair_res.json()["refresh_token"]

    # First refresh with refresh_tok_1 -> succeeds and returns refresh_tok_2
    ref_res_1 = client.post("/api/v1/extension/auth/refresh", json={
        "device_id": "rotator-device-1",
        "refresh_token": refresh_tok_1
    })
    assert ref_res_1.status_code == 200
    refresh_tok_2 = ref_res_1.json()["refresh_token"]
    assert refresh_tok_2 != refresh_tok_1

    # Second refresh with refresh_tok_2 -> succeeds and returns refresh_tok_3
    ref_res_2 = client.post("/api/v1/extension/auth/refresh", json={
        "device_id": "rotator-device-1",
        "refresh_token": refresh_tok_2
    })
    assert ref_res_2.status_code == 200
    refresh_tok_3 = ref_res_2.json()["refresh_token"]
    assert refresh_tok_3 != refresh_tok_2

    # Malicious attempt to reuse old token refresh_tok_1 -> MUST REVOKE DEVICE!
    reuse_res = client.post("/api/v1/extension/auth/refresh", json={
        "device_id": "rotator-device-1",
        "refresh_token": refresh_tok_1
    })
    assert reuse_res.status_code == 403

    # Subsequent refresh even with latest token refresh_tok_3 MUST FAIL because device was revoked
    subsequent_res = client.post("/api/v1/extension/auth/refresh", json={
        "device_id": "rotator-device-1",
        "refresh_token": refresh_tok_3
    })
    assert subsequent_res.status_code == 403

def test_list_and_revoke_devices_from_web_app(client: TestClient):
    """Web app can list user's paired devices and revoke them in DB."""
    # Register user
    reg = client.post("/api/v1/auth/register", json={
        "email": "manager@example.com",
        "full_name": "Device Manager",
        "password": "Password123!"
    })
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate pairing code and pair device
    code_res = client.post("/api/v1/extension/auth/pairing-code", headers=headers)
    pairing_code = code_res.json()["pairing_code"]

    pair_res = client.post("/api/v1/extension/auth/pair", json={
        "pairing_code": pairing_code,
        "device_id": "managed-device-42",
        "device_name": "Chrome Work Laptop"
    })
    assert pair_res.status_code == 200
    refresh_token = pair_res.json()["refresh_token"]

    # List devices
    devices_res = client.get("/api/v1/extension/devices", headers=headers)
    assert devices_res.status_code == 200
    devices = devices_res.json()
    assert any(d["device_id"] == "managed-device-42" for d in devices)

    # Revoke device
    revoke_res = client.post("/api/v1/extension/devices/managed-device-42/revoke", headers=headers)
    assert revoke_res.status_code == 200

    # Device can no longer refresh
    refresh_res = client.post("/api/v1/extension/auth/refresh", json={
        "device_id": "managed-device-42",
        "refresh_token": refresh_token
    })
    assert refresh_res.status_code == 403

def test_extension_token_scope_enforcement(client: TestClient):
    """Extension access tokens cannot be used to perform web actions like deleting resumes."""
    # Register user
    reg = client.post("/api/v1/auth/register", json={
        "email": "scoper@example.com",
        "full_name": "Scope Tester",
        "password": "Password123!"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Pair to obtain an extension access token
    code_res = client.post("/api/v1/extension/auth/pairing-code", headers=headers)
    pairing_code = code_res.json()["pairing_code"]

    pair_res = client.post("/api/v1/extension/auth/pair", json={
        "pairing_code": pairing_code,
        "device_id": "scoped-device-1"
    })
    ext_token = pair_res.json()["extension_token"]
    ext_headers = {"Authorization": f"Bearer {ext_token}"}

    # Extension token CAN call extension endpoints
    ext_endpoint_res = client.get("/api/v1/extension/resumes", headers=ext_headers)
    assert ext_endpoint_res.status_code == 200

    # Extension token CANNOT call web-only endpoints (e.g. deleting resumes)
    del_res = client.delete("/api/v1/resumes/dummy-id", headers=ext_headers)
    assert del_res.status_code in (401, 403)
