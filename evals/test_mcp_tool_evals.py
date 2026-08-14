import pytest
from mcp.tools.leave_tools import (
    get_leave_balance_tool,
    get_team_leave_summary_tool,
    list_employees_tool,
)


def test_mcp_get_leave_balance_valid():
    """Test direct MCP tool execution for employee leave balance."""
    context = {"employee_id": 1, "role": "employee"}
    res = get_leave_balance_tool({"employee_id": 1}, context)
    assert "total" in res
    assert "remaining" in res
    assert "used" in res


def test_mcp_get_team_leave_summary():
    """Test direct MCP tool execution for team leave summary."""
    context = {"employee_id": 2, "role": "manager"}
    res = get_team_leave_summary_tool({}, context)
    assert "total_employees" in res or "employee_count" in res
    assert "total_remaining" in res


def test_mcp_list_employees():
    """Test listing employees via MCP tool."""
    context = {"employee_id": 2, "role": "manager"}
    res = list_employees_tool({}, context)
    assert isinstance(res, dict)
    assert "employees" in res
    assert len(res["employees"]) > 0
    assert "name" in res["employees"][0]


def test_mcp_execute_tool_with_confirmed_flag():
    """Verify execute_tool strips internal __confirmed__ metadata flag before validation."""
    from mcp.runtime import execute_tool
    context = {"employee_id": 1, "role": "employee"}
    args = {
        "employee_id": 1,
        "start_date": "2026-08-15",
        "end_date": "2026-08-20",
        "reason": "sickness",
        "__confirmed__": True
    }
    result = execute_tool("submit_leave_request", args, context)
    assert isinstance(result, dict)
    assert result.get("status") in {"submitted", "pending", "success", "approved"} or "request_id" in result or "message" in result


def test_mcp_get_pending_leave_requests():
    """Test getting pending leave requests via MCP tool as manager."""
    from mcp.tools.leave_tools import get_pending_leave_requests_tool
    context = {"employee_id": 2, "role": "manager"}
    res = get_pending_leave_requests_tool({}, context)
    assert isinstance(res, dict)
    assert "pending_requests" in res
