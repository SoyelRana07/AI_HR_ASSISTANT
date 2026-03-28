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
)
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
    return get_team_leave_summary()


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
    description="Get employees with low remaining leave balance",
    parameters={"threshold": "int"},
    input_model=GetLowLeaveAlertsArgs,
    required_role="manager",
)
def get_low_leave_alerts_tool(args, context):
    return get_low_leave_alerts(args.get("threshold", 3))


@register_tool(
    name="get_leave_leaderboard",
    description="Get top leave users leaderboard",
    parameters={"limit": "int"},
    input_model=GetLeaveLeaderboardArgs,
    required_role="manager",
)
def get_leave_leaderboard_tool(args, context):
    return get_leave_leaderboard(args.get("limit", 5))


@register_tool(
    name="list_employees",
    description="List employees directory",
    parameters={"limit": "int"},
    input_model=ListEmployeesArgs,
    required_role="manager",
)
def list_employees_tool(args, context):
    return list_employees(args.get("limit", 20))


@register_tool(
    name="search_employees",
    description="Search employees by name or email",
    parameters={"query": "str", "limit": "int"},
    input_model=SearchEmployeesArgs,
    required_role="manager",
)
def search_employees_tool(args, context):
    return search_employees(args.get("query"), args.get("limit", 20))


@register_tool(
    name="get_role_breakdown",
    description="Get employee count by role",
    parameters={},
    input_model=GetRoleBreakdownArgs,
    required_role="manager",
)
def get_role_breakdown_tool(args, context):
    return get_role_breakdown()


@register_tool(
    name="get_manager_leave_dashboard",
    description="Get manager dashboard with leave summary, alerts, and leaderboard",
    parameters={"alert_threshold": "int", "leaderboard_limit": "int"},
    input_model=GetManagerLeaveDashboardArgs,
    required_role="manager",
)
def get_manager_leave_dashboard_tool(args, context):
    return get_manager_leave_dashboard(
        args.get("alert_threshold", 3),
        args.get("leaderboard_limit", 5),
    )