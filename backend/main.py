# backend/main.py

import os

from fastapi import Depends, FastAPI, HTTPException, Request, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from pydantic import BaseModel
from llm.router import route_query
from backend.repository.leave_repo import get_leave_balance
from backend.auth import authenticate_user, create_access_token, get_current_user
from env_config import inspect_env_groups, load_project_env
import mcp.tools.leave_tools

load_project_env(__file__)

from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from backend.repository.chat_repo import save_chat_message, get_chat_history, clear_chat_history

class Query(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    history: list[dict] = []

class LoginRequest(BaseModel):
    employee_id: int
    password: str

class ConfirmedQuery(BaseModel):
    tool_name: str
    tool_args: dict
    history: list[dict] = []

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "AI HR Assistant API is running",
        "endpoints": ["/auth/login", "/me", "/chat", "/conversations/{session_id}", "/leave/{employee_id}", "/health/config", "/docs"]
    }


@app.get("/health/config")
def config_health():
    report = inspect_env_groups(CONFIG_REQUIREMENTS)
    return {
        "status": "ok" if report["ok"] else "missing_config",
        "report": report,
    }


@app.post("/auth/login")
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest):
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
@limiter.limit("20/minute")
def chat(request: Request, q: Query, current_user=Depends(get_current_user)):
    employee_id = int(current_user["employee_id"])
    role = str(current_user["role"])
    session_id = q.session_id or "default"

    # Fetch persistent chat history if not provided in payload
    history = q.history
    if not history and session_id:
        history = get_chat_history(session_id, employee_id)

    # Save incoming user message
    save_chat_message(session_id, employee_id, "user", q.message)

    routed = route_query(
        q.message,
        employee_id,
        role,
        history,
        include_debug=True,
    )

    final_response = routed
    routing_debug = {}

    if isinstance(routed, dict):
        if routed.get("status") == "requires_confirmation":
            return routed
        if "data" in routed and "routing_debug" in routed:
            final_response = routed["data"]
            routing_debug = routed["routing_debug"]

    # Save assistant response to DB
    response_text = str(final_response)
    save_chat_message(session_id, employee_id, "assistant", response_text)

    return {
        "response": final_response,
        "routing_debug": routing_debug,
        "session_id": session_id,
    }


@app.get("/conversations/{session_id}")
def get_conversation(session_id: str, current_user=Depends(get_current_user)):
    employee_id = int(current_user["employee_id"])
    messages = get_chat_history(session_id, employee_id)
    return {"session_id": session_id, "messages": messages}


@app.delete("/conversations/{session_id}")
def delete_conversation(session_id: str, current_user=Depends(get_current_user)):
    employee_id = int(current_user["employee_id"])
    count = clear_chat_history(session_id, employee_id)
    return {"session_id": session_id, "deleted_count": count, "message": "Conversation history cleared."}


@app.post("/execute_tool")
def execute_tool(q: ConfirmedQuery, current_user=Depends(get_current_user)):
    # Inject confirmation flag
    q.tool_args["__confirmed__"] = True
    
    # We call route_query again but this time the LLM choice is bypassed 
    # Or we can just call call_tool directly. 
    # But route_query handles the loop logic. 
    # Actually, we should probably have a tool execution path that just runs the tool.
    
    from mcp.client import call_tool
    try:
        result = call_tool(
            q.tool_name,
            q.tool_args,
            {"employee_id": int(current_user["employee_id"]), "role": str(current_user["role"])}
        )
        return {"response": result}
    except Exception as e:
        return {"response": {"error": str(e)}}


@app.get("/leave/{employee_id}")
def leave_balance(employee_id: int, current_user=Depends(get_current_user)):
    if current_user["role"] != "manager" and current_user["employee_id"] != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own leave balance",
        )

    return get_leave_balance(employee_id)

