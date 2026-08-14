import pytest
from llm.router import _extract_employee_id_from_text, extract_json, _normalize_decision


def test_extract_employee_id_from_text():
    """Verify regex extraction of employee IDs from natural language queries."""
    assert _extract_employee_id_from_text("show leave balance for employee 4") == 4
    assert _extract_employee_id_from_text("details for id: 12") == 12
    assert _extract_employee_id_from_text("employee #105 balance") == 105
    assert _extract_employee_id_from_text("show my leave balance") is None


def test_extract_json_clean_markdown():
    """Verify parsing of clean and markdown-wrapped JSON strings."""
    raw_markdown = '```json\n{"action": "get_leave_balance", "action_input": {}}\n```'
    parsed = extract_json(raw_markdown)
    assert parsed.get("action") == "get_leave_balance"


def test_extract_json_fallback_intent():
    """Verify fallback tool intent detection when LLM emits natural language instead of pure JSON."""
    raw_text = "I will use get_leave_balance to check the details for the user."
    parsed = extract_json(raw_text)
    assert parsed.get("action") == "get_leave_balance"


def test_normalize_decision_legacy_tool():
    """Verify normalization of legacy/hallucinated LLM response keys."""
    legacy = {"tool": "get_leave_balance", "args": {"employee_id": 1}}
    normalized = _normalize_decision(legacy)
    assert "action" in normalized or "final_answer" in normalized


def test_humanize_response_raw_fallback():
    """Verify _humanize_response does not crash with NameError when raw fallback is hit."""
    from llm.router import _humanize_response
    raw_json = '{"unknown_nested": {"foo": "bar"}}'
    result = _humanize_response(raw_json, "test query")
    assert result == raw_json or isinstance(result, str)


def test_try_fast_path_route_matching():
    """Verify regex fast path intent matching for common queries."""
    from llm.router import _try_fast_path_route

    # Employee queries
    res = _try_fast_path_route("show my leave balance", employee_id=1, role="employee")
    assert res is not None
    assert res[0] == "get_leave_balance"
    assert res[1]["employee_id"] == 1

    # Manager queries
    res_mgr = _try_fast_path_route("pending leave requests", employee_id=1, role="manager")
    assert res_mgr is not None
    assert res_mgr[0] == "get_pending_leave_requests"

    # Employee attempting manager query should get None (falling back to standard RBAC flow)
    res_emp = _try_fast_path_route("pending leave requests", employee_id=1, role="employee")
    assert res_emp is None


