import pytest
from llm.router import route_query


def test_employee_scope_guardrail_forbidden():
    """Verify that an employee requesting data for another employee ID is blocked with FORBIDDEN_EMPLOYEE_SCOPE."""
    result = route_query(
        user_input="show leave balance for employee 4",
        employee_id=1,  # Authenticated as Employee 1
        role="employee",
        include_debug=True
    )
    
    data = result.get("data", result)
    assert isinstance(data, dict)
    assert data.get("code") == "FORBIDDEN_EMPLOYEE_SCOPE"
    assert data.get("error") == "Access denied"


def test_employee_own_scope_allowed():
    """Verify that an employee requesting their own leave details is allowed without scope violations."""
    # When employee asks for their own ID (1), scope validation passes
    result = route_query(
        user_input="show leave balance for employee 1",
        employee_id=1,
        role="employee",
        include_debug=True
    )
    
    data = result.get("data", result)
    # Should not be blocked by security scope guardrail
    if isinstance(data, dict):
        assert data.get("code") != "FORBIDDEN_EMPLOYEE_SCOPE"
