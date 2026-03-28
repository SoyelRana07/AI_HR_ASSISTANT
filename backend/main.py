# backend/main.py

import os

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from llm.router import route_query
from backend.repository.leave_repo import get_leave_balance
from backend.auth import authenticate_user, create_access_token, get_current_user
from env_config import inspect_env_groups, load_project_env
import mcp.tools.leave_tools

load_project_env(__file__)

CONFIG_REQUIREMENTS = {
    "database": ["DATABASE_URL", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"],
    "mcp": ["MCP_MODE", "MCP_TIMEOUT_SECONDS", "MCP_STRICT_REMOTE"],
    "mcp_remote": ["MCP_SERVER_URL"] if os.getenv("MCP_MODE", "").lower() == "remote" else [],
    "llm": ["OLLAMA_URL", "OLLAMA_MODEL", "OLLAMA_TIMEOUT_SECONDS"],
    "router": ["ROUTER_RULES_PATH"],
    "frontend": ["BACKEND_CHAT_URL"],
}

app = FastAPI()

class Query(BaseModel):
    message: str


class LoginRequest(BaseModel):
    employee_id: int
    password: str

@app.get("/")
def root():
    return {
        "message": "AI HR Assistant API is running",
        "endpoints": ["/auth/login", "/me", "/chat", "/leave/{employee_id}", "/health/config", "/docs"]
    }


@app.get("/health/config")
def config_health():
    report = inspect_env_groups(CONFIG_REQUIREMENTS)
    return {
        "status": "ok" if report["ok"] else "missing_config",
        "report": report,
    }


@app.post("/auth/login")
def login(payload: LoginRequest):
    user = authenticate_user(payload.employee_id, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid employee ID or password",
        )

    access_token = create_access_token(
        {
            "employee_id": user.id,
            "role": user.role,
            "name": user.name,
            "email": user.email,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "employee_id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }


@app.get("/me")
def me(current_user=Depends(get_current_user)):
    return {"user": current_user}


@app.post("/chat")
def chat(q: Query, current_user=Depends(get_current_user)):
    routed = route_query(
        q.message,
        int(current_user["employee_id"]),
        str(current_user["role"]),
        include_debug=True,
    )

    if isinstance(routed, dict) and "data" in routed and "routing_debug" in routed:
        return {
            "response": routed["data"],
            "routing_debug": routed["routing_debug"],
        }

    return {
        "response": routed,
        "routing_debug": {},
    }


@app.get("/leave/{employee_id}")
def leave_balance(employee_id: int, current_user=Depends(get_current_user)):
    if current_user["role"] != "manager" and current_user["employee_id"] != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own leave balance",
        )

    return get_leave_balance(employee_id)

