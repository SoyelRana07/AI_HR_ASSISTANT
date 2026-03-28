from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from mcp.registry import get_tools_metadata
from mcp.runtime import ToolCallError, execute_tool
import mcp.tools.leave_tools  # noqa: F401 - ensures tool registration on startup

app = FastAPI(title="AI HR MCP Server")


class CallToolRequest(BaseModel):
    name: str
    args: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


def call_tool(name, args, context):
    return execute_tool(name, args, context)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tools")
def list_tools():
    return get_tools_metadata()


@app.post("/call")
def call_tool_endpoint(payload: CallToolRequest):
    try:
        result = call_tool(payload.name, payload.args, payload.context)
        return {"ok": True, "data": result}
    except ToolCallError as exc:
        status_code = {
            "TOOL_NOT_FOUND": 404,
            "INVALID_ARGUMENTS": 400,
            "FORBIDDEN_TOOL": 403,
            "TOOL_EXECUTION_FAILED": 500,
        }.get(exc.code, 500)
        return JSONResponse(status_code=status_code, content=exc.to_payload())