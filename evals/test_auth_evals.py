import time
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.auth import (
    create_access_token,
    decode_access_token,
    get_current_user,
)


def test_auth_valid_token_decode():
    """Verify that a valid token can be created and decoded with claims intact."""
    token = create_access_token({"employee_id": 1, "role": "employee", "name": "Alice", "email": "alice@company.com"})
    decoded = decode_access_token(token)
    assert decoded["employee_id"] == 1
    assert decoded["role"] == "employee"
    assert decoded["name"] == "Alice"


def test_auth_get_current_user_success():
    """Verify get_current_user extracts user dict from HTTP Bearer credentials."""
    token = create_access_token({"employee_id": 1, "role": "employee", "name": "Alice", "email": "alice@company.com"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = get_current_user(creds)
    assert user["employee_id"] == 1
    assert user["role"] == "employee"
    assert user["name"] == "Alice"


def test_auth_missing_credentials_raises_401():
    """Verify missing credentials raises 401 Unauthorized."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(None)
    assert exc_info.value.status_code == 401
    assert "Missing bearer token" in exc_info.value.detail


def test_auth_invalid_token_raises_401():
    """Verify malformed token raises 401 Unauthorized."""
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.str")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(creds)
    assert exc_info.value.status_code == 401


def test_auth_expired_token_raises_401():
    """Verify expired token raises 401 Unauthorized."""
    token = create_access_token({"employee_id": 1, "role": "employee"}, expires_in=-100)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(creds)
    assert exc_info.value.status_code == 401
    assert "Authentication token expired" in exc_info.value.detail
