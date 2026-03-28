# llm/router.py

import json
import re

from llm.engine import ask_llm
from mcp.client import call_tool, get_tools_metadata


def _extract_employee_id_from_text(text: str):
    patterns = [
        r"employee\s*(?:id)?\s*[:#-]?\s*(\d+)",
        r"id\s*[:#-]?\s*(\d+)",
        r"\b(\d{1,6})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                value = int(match.group(1))
                if value > 0:
                    return value
            except (TypeError, ValueError):
                continue

    return None


def _extract_balanced_json_blocks(text: str):
    blocks = []
    stack = []
    start = None

    opening = {"{": "}", "[": "]"}
    closing = {"}": "{", "]": "["}

    for idx, ch in enumerate(text):
        if ch in opening:
            if not stack:
                start = idx
            stack.append(ch)
        elif ch in closing and stack:
            if stack[-1] == closing[ch]:
                stack.pop()
                if not stack and start is not None:
                    blocks.append(text[start: idx + 1])
                    start = None
            else:
                stack = []
                start = None

    return blocks


def extract_json(text):
    clean_text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(clean_text)
    except (json.JSONDecodeError, TypeError):
        pass

    for block in _extract_balanced_json_blocks(clean_text):
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            continue

    print("FAILED TO PARSE LLM OUTPUT:")
    print(clean_text)
    return {"message": "LLM output invalid"}


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_decision(decision):
    if isinstance(decision, list):
        for item in decision:
            if isinstance(item, dict) and ("tool" in item or "message" in item):
                decision = item
                break
        else:
            return {"message": "Invalid response"}

    if not isinstance(decision, dict):
        return {"message": "Invalid response"}

    if "tool" in decision:
        if "parameters" in decision and "args" not in decision:
            decision["args"] = decision.pop("parameters")

        if "args" not in decision or not isinstance(decision["args"], dict):
            decision["args"] = {}

        if "employee_id" in decision:
            decision["args"]["employee_id"] = decision.pop("employee_id")

    return decision


def _tools_for_prompt(tools):
    simplified = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue

        simplified.append(
            {
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {}),
                "required_role": tool.get("required_role"),
            }
        )

    return simplified


def _is_non_actionable_message(decision):
    message = decision.get("message")
    if not isinstance(message, str):
        return False

    normalized = message.strip().lower()
    return normalized in {"text", "message", "n/a", "unknown", "invalid response"}


def _strip_none_values(payload):
    if not isinstance(payload, dict):
        return {}
    return {key: value for key, value in payload.items() if value is not None}


def _choose_tool_with_llm(user_input: str, tools, role: str):
    tools_for_prompt = _tools_for_prompt(tools)

    prompt = f"""
You are a backend JSON tool router.

Your job is to select the best tool from AVAILABLE TOOLS using semantic intent,
not keyword matching.

You MUST return ONLY valid JSON.
DO NOT explain.
DO NOT use markdown.
DO NOT wrap in ```.

STRICT FORMAT:

Tool call:
{{"tool":"tool_name","args":{{}}}}

Message:
{{"message":"text"}}

AVAILABLE TOOLS:
{json.dumps(tools_for_prompt)}

USER ROLE:
{role}

RULES:
- Use ONLY tool names from AVAILABLE TOOLS.
- NEVER invent tool names.
- ALWAYS include "args" when returning a tool.
- Prefer empty args {{}} if not required.
- If no tool can answer, return a clear message JSON.
- Do NOT return placeholder values like {{"message":"text"}}.
- Output MUST start with {{ and end with }}.
- NO extra text before or after JSON.

USER REQUEST:
{user_input}
"""

    llm_output = ask_llm(prompt)

    print("\n===== LLM RAW OUTPUT =====")
    print(llm_output)
    print("==========================\n")

    return _normalize_decision(extract_json(llm_output))


def _repair_tool_choice_with_llm(user_input: str, tools, invalid_tool: str, role: str):
    tools_for_prompt = _tools_for_prompt(tools)

    prompt = f"""
Your previous decision was invalid.

INVALID DECISION:
{invalid_tool}

You MUST choose again from AVAILABLE TOOLS.
Return ONLY valid JSON, no explanation.

STRICT FORMAT:
{{"tool":"tool_name","args":{{}}}}
or
{{"message":"text"}}

AVAILABLE TOOLS:
{json.dumps(tools_for_prompt)}

USER ROLE:
{role}

USER REQUEST:
{user_input}
"""

    llm_output = ask_llm(prompt)

    print("\n===== LLM RETRY OUTPUT =====")
    print(llm_output)
    print("============================\n")

    return _normalize_decision(extract_json(llm_output))


def _fallback_message():
    return {"message": "Sorry, I couldn't process that request."}


def _with_optional_debug(result, routing_debug, include_debug: bool):
    if not include_debug:
        return result
    return {
        "data": result,
        "routing_debug": routing_debug,
    }


def route_query(user_input: str, employee_id: int, role: str, include_debug: bool = False):
    tools = get_tools_metadata()
    print("LOADED TOOLS:", tools)

    requested_employee_id = _extract_employee_id_from_text(user_input)
    routing_debug = {
        "role": role,
        "current_employee_id": employee_id,
        "requested_employee_id": requested_employee_id,
        "selected_tool": None,
        "selected_args": {},
        "repair_attempted": False,
    }

    if role == "employee" and requested_employee_id and requested_employee_id != employee_id:
        result = {
            "error": "Access denied",
            "code": "FORBIDDEN_EMPLOYEE_SCOPE",
            "details": {
                "requested_employee_id": requested_employee_id,
                "current_employee_id": employee_id,
            },
            "message": "Employees can only access their own leave information.",
        }
        return _with_optional_debug(result, routing_debug, include_debug)

    if not isinstance(tools, list) or not tools:
        result = {"message": "No tools are available for routing right now."}
        return _with_optional_debug(result, routing_debug, include_debug)

    tool_map = {
        tool.get("name"): tool for tool in tools if isinstance(tool, dict) and tool.get("name")
    }

    available_tool_names = {tool["name"] for tool in tools}

    decision = _choose_tool_with_llm(user_input, tools, role)

    if "message" in decision and _is_non_actionable_message(decision):
        print("NON-ACTIONABLE MESSAGE FROM LLM:", decision.get("message"))
        routing_debug["repair_attempted"] = True
        decision = _repair_tool_choice_with_llm(
            user_input,
            tools,
            f"placeholder message: {decision.get('message')}",
            role,
        )

    if "tool" in decision and decision["tool"] not in available_tool_names:
        print("INVALID TOOL FROM LLM:", decision["tool"])
        routing_debug["repair_attempted"] = True
        decision = _repair_tool_choice_with_llm(
            user_input,
            tools,
            decision["tool"],
            role,
        )

    if "tool" in decision and decision["tool"] not in available_tool_names:
        print("INVALID TOOL AFTER RETRY:", decision["tool"])
        decision = _fallback_message()

    if decision.get("message") == "LLM output invalid":
        decision = _fallback_message()

    if "tool" not in decision and "message" not in decision:
        decision = _fallback_message()

    if "tool" in decision:
        tool_name = decision["tool"]
        tool_meta = tool_map.get(tool_name, {})
        tool_parameters = tool_meta.get("parameters", {})

        if not isinstance(decision.get("args"), dict):
            decision["args"] = {}

        decision["args"] = _strip_none_values(decision["args"])

        if "employee_id" in tool_parameters:
            if role == "employee":
                decision["args"]["employee_id"] = employee_id
            else:
                decision["args"]["employee_id"] = requested_employee_id or decision["args"].get(
                    "employee_id", employee_id
                )

            decision["args"]["employee_id"] = _to_int(
                decision["args"].get("employee_id"), employee_id
            )

        routing_debug["selected_tool"] = decision["tool"]
        routing_debug["selected_args"] = dict(decision["args"])

        result = call_tool(
            decision["tool"],
            decision["args"],
            {"employee_id": employee_id, "role": role},
        )

        return _with_optional_debug(result, routing_debug, include_debug)

    return _with_optional_debug(decision, routing_debug, include_debug)
