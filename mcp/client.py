import os
from typing import Any, Dict, List

import requests

from env_config import get_required_env, load_project_env
from mcp.registry import get_tools_metadata as get_local_tools_metadata
from mcp.runtime import ToolCallError, execute_tool

load_project_env(__file__)
required = get_required_env(["MCP_MODE", "MCP_TIMEOUT_SECONDS", "MCP_STRICT_REMOTE"])

MCP_MODE = required["MCP_MODE"].lower()
if MCP_MODE not in {"local", "remote"}:
    raise RuntimeError("MCP_MODE must be either 'local' or 'remote'")

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
MCP_TIMEOUT_SECONDS = float(required["MCP_TIMEOUT_SECONDS"])
MCP_STRICT_REMOTE = required["MCP_STRICT_REMOTE"] == "1"


def _call_tool_local(name: str, args: Dict[str, Any], context: Dict[str, Any]):
    try:
        return execute_tool(name, args, context)
    except ToolCallError as exc:
        return {"error": exc.message, "code": exc.code, "details": exc.details}


def _call_tool_remote(name: str, args: Dict[str, Any], context: Dict[str, Any]):
    if not MCP_SERVER_URL:
        return {
            "error": "MCP_SERVER_URL is required in remote mode",
            "code": "REMOTE_URL_MISSING",
            "details": {},
        }

    response = requests.post(
        f"{MCP_SERVER_URL}/call",
        json={"name": name, "args": args, "context": context},
        timeout=MCP_TIMEOUT_SECONDS,
    )
    payload = response.json()

    if response.status_code >= 400 or not payload.get("ok", False):
        error = payload.get("error", {})
        return {
            "error": error.get("message", "MCP remote call failed"),
            "code": error.get("code", "REMOTE_CALL_FAILED"),
            "details": error.get("details", {}),
        }

    return payload.get("data")


def _get_tools_remote() -> List[Dict[str, Any]]:
    if not MCP_SERVER_URL:
        raise requests.RequestException("MCP_SERVER_URL is required in remote mode")

    response = requests.get(
        f"{MCP_SERVER_URL}/tools",
        timeout=MCP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def get_tools_metadata() -> List[Dict[str, Any]]:
    if MCP_MODE != "remote":
        return get_local_tools_metadata()

    try:
        return _get_tools_remote()
    except requests.RequestException as exc:
        if MCP_STRICT_REMOTE:
            return []
        print(f"MCP remote tool metadata failed, falling back to local: {exc}")
        return get_local_tools_metadata()


def call_tool(name: str, args: Dict[str, Any], context: Dict[str, Any]):
    if MCP_MODE != "remote":
        return _call_tool_local(name, args, context)

    try:
        return _call_tool_remote(name, args, context)
    except requests.RequestException as exc:
        if MCP_STRICT_REMOTE:
            return {
                "error": "MCP remote call failed",
                "code": "REMOTE_UNAVAILABLE",
                "details": {"reason": str(exc)},
            }
        print(f"MCP remote call failed, falling back to local: {exc}")
        return _call_tool_local(name, args, context)
