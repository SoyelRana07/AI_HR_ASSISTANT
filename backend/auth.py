import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.db import SessionLocal
from backend.models import Employee


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _get_secret() -> str:
    # Local default keeps development friction low; set AUTH_SECRET in real deployments.
    return os.getenv("AUTH_SECRET", "dev-only-change-me")


def _get_expiry_seconds() -> int:
    raw = os.getenv("AUTH_TOKEN_EXPIRE_SECONDS", "3600")
    try:
        value = int(raw)
    except ValueError:
        value = 3600
    return max(300, value)


def create_access_token(claims: Dict[str, str | int]) -> str:
    payload = dict(claims)
    payload["exp"] = int(time.time()) + _get_expiry_seconds()
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url_encode(payload_json)

    signature = hmac.new(
        _get_secret().encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64url_encode(signature)
    return f"{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Dict[str, str | int]:
    try:
        payload_b64, sig_b64 = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    expected_sig = hmac.new(
        _get_secret().encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).digest()

    provided_sig = _b64url_decode(sig_b64)
    if not hmac.compare_digest(expected_sig, provided_sig):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token expired",
        )

    return payload


def authenticate_user(employee_id: int, password: str) -> Optional[Employee]:
    db = SessionLocal()
    try:
        user = db.query(Employee).filter(Employee.id == employee_id).first()
        if not user:
            return None

        shared_password = os.getenv("AUTH_SHARED_PASSWORD")
        if shared_password:
            valid_password = password == shared_password
        else:
            # Development default: password is zero-padded employee id.
            valid_password = password == f"{employee_id:04d}"

        if not valid_password:
            return None

        return user
    finally:
        db.close()


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Dict[str, str | int]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    claims = decode_access_token(credentials.credentials)
    employee_id = claims.get("employee_id")
    role = claims.get("role")
    name = claims.get("name")
    email = claims.get("email")

    if not isinstance(employee_id, int) or not isinstance(role, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    return {
        "employee_id": employee_id,
        "role": role,
        "name": name if isinstance(name, str) else "",
        "email": email if isinstance(email, str) else "",
    }