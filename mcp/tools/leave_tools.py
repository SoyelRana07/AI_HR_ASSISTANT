from backend.repository.leave_repo import (
    get_manager_leave_dashboard,
    get_role_breakdown,
    get_employee_leave_details,
    get_leave_balance,
    get_leave_leaderboard,
    list_employees,
    get_low_leave_alerts,
    search_employees,
    get_team_leave_summary,
    create_leave_request,
    approve_leave_request,
)
from datetime import date
from mcp.registry import register_tool
from mcp.tools.schemas import (
    GetManagerLeaveDashboardArgs,
    GetEmployeeLeaveDetailsArgs,
    GetLeaveBalanceArgs,
    GetLeaveLeaderboardArgs,
    GetLowLeaveAlertsArgs,
    GetRoleBreakdownArgs,
    ListEmployeesArgs,
    SearchEmployeesArgs,
    GetTeamLeaveSummaryArgs,
    SubmitLeaveRequestArgs,
    ApproveLeaveRequestArgs,
)

@register_tool(
    name="get_leave_balance",
    description="Get leave balance of employee",
    parameters={"employee_id": "int"},
    input_model=GetLeaveBalanceArgs,
)
def get_leave_balance_tool(args, context):
    employee_id = args.get("employee_id", context["employee_id"])
    return get_leave_balance(employee_id)


@register_tool(
    name="get_team_leave_summary",
    description="Get leave usage summary across all employees",
    parameters={},
    input_model=GetTeamLeaveSummaryArgs,
    required_role="manager",
)
def get_team_leave_summary_tool(args, context):
    return get_team_leave_summary(context["employee_id"])


@register_tool(
    name="get_employee_leave_details",
    description="Get employee profile and leave details",
    parameters={"employee_id": "int"},
    input_model=GetEmployeeLeaveDetailsArgs,
)
def get_employee_leave_details_tool(args, context):
    employee_id = args.get("employee_id", context["employee_id"])
    return get_employee_leave_details(employee_id)


@register_tool(
    name="get_low_leave_alerts",
    description="Get employees running out of leave (balance <= threshold). Do NOT use this to find the single lowest leave. If you want the lowest leave balance, use get_leave_leaderboard instead.",
    parameters={"threshold": "int (default: 3)"},
    input_model=GetLowLeaveAlertsArgs,
    required_role="manager",
)
def get_low_leave_alerts_tool(args, context):
    return get_low_leave_alerts(context["employee_id"], args.get("threshold", 3))


@register_tool(
    name="get_leave_leaderboard",
    description="Get the leaderboard of employees sorted by highest leave used (which means LOWEST leave remaining). Use this tool to answer queries about who has the most or least leave.",
    parameters={"limit": "int (default: 5)"},
    input_model=GetLeaveLeaderboardArgs,
    required_role="manager",
)
def get_leave_leaderboard_tool(args, context):
    return get_leave_leaderboard(context["employee_id"], args.get("limit", 5))


@register_tool(
    name="list_employees",
    description="List employees directory",
    parameters={"limit": "int"},
    input_model=ListEmployeesArgs,
    required_role="manager",
)
def list_employees_tool(args, context):
    return list_employees(context["employee_id"], args.get("limit", 20))


@register_tool(
    name="search_employees",
    description="Search employees by name or email. You MUST provide a 'query' string of length >= 1.",
    parameters={"query": "string (required)", "limit": "int (optional)"},
    input_model=SearchEmployeesArgs,
    required_role="manager",
)
def search_employees_tool(args, context):
    return search_employees(context["employee_id"], args.get("query"), args.get("limit", 20))


@register_tool(
    name="get_role_breakdown",
    description="Get employee count by role",
    parameters={},
    input_model=GetRoleBreakdownArgs,
    required_role="manager",
)
def get_role_breakdown_tool(args, context):
    return get_role_breakdown(context["employee_id"])


@register_tool(
    name="get_manager_leave_dashboard",
    description="Get manager dashboard with leave summary, alerts, and leaderboard",
    parameters={"alert_threshold": "int", "leaderboard_limit": "int"},
    input_model=GetManagerLeaveDashboardArgs,
    required_role="manager",
)
def get_manager_leave_dashboard_tool(args, context):
    return get_manager_leave_dashboard(
        context["employee_id"],
        args.get("alert_threshold", 3),
        args.get("leaderboard_limit", 5),
    )


@register_tool(
    name="submit_leave_request",
    description="Submit a new leave request. Requires confirmation.",
    parameters={
        "employee_id": "int",
        "start_date": "string (YYYY-MM-DD)",
        "end_date": "string (YYYY-MM-DD)",
        "reason": "string"
    },
    input_model=SubmitLeaveRequestArgs,
    requires_confirmation=True,
)
def submit_leave_request_tool(args, context):
    try:
        start_dt = date.fromisoformat(args["start_date"])
        end_dt = date.fromisoformat(args["end_date"])
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}
    
    return create_leave_request(
        args.get("employee_id", context["employee_id"]),
        start_dt,
        end_dt,
        args["reason"]
    )


@register_tool(
    name="approve_leave_request",
    description="Approve or reject a leave request. Manager only. Requires confirmation.",
    parameters={
        "request_id": "int",
        "approve": "boolean (default: true)"
    },
    input_model=ApproveLeaveRequestArgs,
    required_role="manager",
    requires_confirmation=True,
)
def approve_leave_request_tool(args, context):
    return approve_leave_request(
        context["employee_id"],
        args["request_id"],
        args.get("approve", True)
    )
