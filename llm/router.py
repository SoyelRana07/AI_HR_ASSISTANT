# llm/router.py

import json
import re

from llm.engine import ask_llm
from llm.schemas import AgentAction, AgentFinish
from llm.state import AgentState
from mcp.client import call_tool, get_tools_metadata
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
import pydantic
import json
import uuid
from langsmith import traceable

def execute_tools(state: AgentState):
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    results = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        args = tool_call["args"]
        
        # Security: Force authorized employee_id
        args["employee_id"] = state["employee_id"]
        
        try:
            observation = call_tool(tool_name, args, {"employee_id": state["employee_id"], "role": state["role"]})
            obs_str = json.dumps(observation)
            if len(obs_str) > 1000:
                obs_str = obs_str[:1000] + "... (truncated)"
        except Exception as e:
            obs_str = json.dumps({"error": str(e)})
            
        results.append(ToolMessage(
            tool_call_id=tool_call["id"],
            content=obs_str
        ))
        
    return {"messages": results}


def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    
    # Loop breaker: limit number of turns
    if len(state["messages"]) > 15:
        return END

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "action"
    return END



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


def extract_json(text: str):
    if not text:
        return {"message": "Empty LLM output"}
    
    # Pre-clean: strip markdown blocks and basic noise
    clean_text = re.sub(r'```(?:json)?', '', text).strip()
    clean_text = re.sub(r'```$', '', clean_text).strip()
    
    # Strategy 1: Direct JSON parse
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Look for anything between { and } (inclusive, longest match)
    match = re.search(r'(\{.*\})', clean_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Balanced brace extraction (most robust for conversational text)
    blocks = _extract_balanced_json_blocks(clean_text)
    for block in blocks:
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            continue

    # Final fallback: try to detect plain-text tool intent
    # e.g. "I will use list_employees to get the team size"
    known_tools = [
        "get_leave_balance", "get_employee_leave_details", "get_leave_leaderboard",
        "list_employees", "search_employees", "get_low_leave_alerts",
        "get_team_leave_summary", "get_role_breakdown", "get_manager_leave_dashboard",
        "submit_leave_request", "approve_leave_request"
    ]
    lower_text = text.lower()
    for tool in known_tools:
        if tool.replace("_", " ") in lower_text or tool in lower_text:
            return {
                "action": tool,
                "action_input": {},
                "thought": f"Detected intent to use {tool}"
            }

    return {"message": text}


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_decision(decision):
    if isinstance(decision, list):
        for item in decision:
            if isinstance(item, dict) and ("action" in item or "final_answer" in item or "message" in item):
                return item
        if decision and isinstance(decision[0], dict):
            return decision[0]
        return {"message": "Invalid response format"}

    if not isinstance(decision, dict):
        return {"message": "Invalid response format"}

    # Consistency mapping
    if "final_answer" in decision and not decision.get("action"):
        pass # Fine
    elif "action" in decision:
        pass # Fine
    elif "message" in decision:
        decision["final_answer"] = decision.pop("message")
    else:
        # If it only has 'thought', treat it as a message or if it's empty
        decision["final_answer"] = decision.get("thought", "I'm sorry, I encountered an error processing that request.")

    return decision

    # Fix legacy "tool" format if LLM hallucinated it
    if "tool" in decision and "action" not in decision:
        decision["action"] = decision.pop("tool")
        decision["action_input"] = decision.pop("args", decision.pop("parameters", {}))
    
    if "action" in decision:
         if "action_input" not in decision or not isinstance(decision["action_input"], dict):
             decision["action_input"] = {}
         
         if "employee_id" in decision:
             decision["action_input"]["employee_id"] = decision.pop("employee_id")

    return decision


def _tools_for_prompt(tools, role):
    simplified = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue

        req_role = tool.get("required_role")
        if req_role == "manager" and role != "manager":
            continue

        simplified.append(
            {
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {}),
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


@traceable(name="AgentStepWithLLM", run_type="llm")
def _agent_step_with_llm(user_input: str, tools, role: str, history: list, observations: list):
    tools_for_prompt = _tools_for_prompt(tools, role)
    history_str = json.dumps(history, indent=2) if history else "[]"
    observations_str = json.dumps(observations, indent=2) if observations else "[]"

    prompt = f"""
You are an autonomous HR AI Agent.
Analyze the user request and decide whether to use a tool or provide a final answer.

OUTPUT FORMAT:
Your output MUST be a single, valid JSON object matching one of these two structures:

FORMAT A (To call a tool):
{{
  "thought": "Reasoning about why this tool is needed",
  "action": "tool_name",
  "action_input": {{"param": "value"}}
}}

FORMAT B (Final Response):
{{
  "thought": "Reasoning about why we have enough info",
  "final_answer": "The final message to the user"
}}

AVAILABLE TOOLS:
{json.dumps(tools_for_prompt, indent=2)}

USER ROLE: {role}
CHAT HISTORY: {history_str}
PREVIOUS OBSERVATIONS: {observations_str}

RULES:
1. ONLY return the JSON. No markdown, no pre-text.
2. If you need data, call a tool.
3. If you have the result, provide a final_answer.
4. If a tool returns an error, try to fix the arguments or explain the issue in final_answer.

USER REQUEST: {user_input}
"""
    llm_output = ask_llm(prompt)
    
    # Try to extract JSON if LLM included markdown
    clean_json = llm_output.strip()
    if clean_json.startswith("```json"):
        clean_json = clean_json.split("```json")[1].split("```")[0].strip()
    elif clean_json.startswith("```"):
        clean_json = clean_json.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(clean_json)
        # Validate with Pydantic
        if "final_answer" in data:
            return AgentFinish.model_validate(data).model_dump()
        else:
            return AgentAction.model_validate(data).model_dump()
    except (json.JSONDecodeError, pydantic.ValidationError) as e:
        print(f"PARSING ERROR: {str(e)}\nOutput was: {llm_output}")
        return {"error": "Invalid agent output structure", "raw": llm_output}


def _fallback_message():
    return {"message": "Sorry, I couldn't process that request."}

def _synthesize_final_after_timeout(user_input: str, history: list, observations: list, role: str):
    observations_str = json.dumps(observations, indent=2) if observations else "[]"
    prompt = f"""You are a helpful HR AI Assistant. The user asked: "{user_input}"

Here is the data you collected from internal tools:
{observations_str}

Write a clean, concise, friendly response directly answering the user's question.

RULES:
- Use ONLY the data above. Do not make up numbers.
- Do NOT mention tools, tool calls, loops, limits, errors, JSON, or internal systems.
- Write in a natural, HR-assistant tone. Use bullet points if listing data.
- If the data is empty or unhelpful, say: "I wasn't able to find that information. Please try again."
- Respond ONLY with the final answer text. No preamble.
"""
    return ask_llm(prompt)


def _polish_response(raw_response: str, user_input: str) -> str:
    """If response looks verbose or contains internal jargon, clean it up."""
    jargon_markers = [
        "FORMAT 2", "loop limit", "time limit", "tool call", "I attempted to use",
        "internal tool", "my system", "PREVIOUS STEPS", "ACTION INPUT"
    ]
    if not any(marker.lower() in raw_response.lower() for marker in jargon_markers):
        return raw_response  # Already clean, skip LLM call

    prompt = f"""Clean up the following HR assistant response. 
Remove any mentions of internal tools, system errors, loop limits, or technical jargon.
Keep ONLY the actual data and present it as a clear, friendly reply to: "{user_input}"

Raw response:
{raw_response}

Write ONLY the cleaned response. No preamble."""
    return ask_llm(prompt)


def _with_optional_debug(result, routing_debug, include_debug: bool):
    if not include_debug:
        return result
    return {
        "data": result,
        "routing_debug": routing_debug,
    }


def _humanize_response(raw: str, user_input: str) -> str:
    """Convert raw JSON/dict strings into clean human-readable markdown text using Python formatting."""
    if not isinstance(raw, str):
        raw = str(raw)
    stripped = raw.strip()
    
    # If already conversational text, return as-is
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return raw
    
    # Try to parse the JSON
    try:
        data = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return raw  # Can't parse, return as-is
    
    return _format_data_as_text(data)


def _format_data_as_text(data) -> str:
    """Recursively format HR data structures into human-readable text."""
    if isinstance(data, str):
        return data

    if isinstance(data, list):
        if not data:
            return "No records found."
        # List of employee-like dicts
        if isinstance(data[0], dict):
            lines = []
            for i, item in enumerate(data, 1):
                lines.append(_format_employee_item(i, item))
            return "\n".join(lines)
        return "\n".join(f"- {v}" for v in data)

    if isinstance(data, dict):
        # Error case
        if "error" in data:
            return f"⚠️ {data['error']}"

        lines = []

        # High-level summary fields
        summary_map = {
            "employee_count": "👥 Total employees",
            "total_employees": "👥 Total employees",
            "total_allocated": "📅 Total leave allocated",
            "total_used": "✅ Total leave used",
            "total_remaining": "🕐 Total leave remaining",
            "avg_remaining": "📊 Avg leave remaining per person",
            "count": "📊 Count",
        }
        for key, label in summary_map.items():
            if key in data:
                val = data[key]
                suffix = " days" if "leave" in key or "remaining" in key or "used" in key or "allocated" in key else ""
                lines.append(f"{label}: **{val}{suffix}**")

        # Roles breakdown
        if "roles" in data and isinstance(data["roles"], list):
            lines.append("\n**Role Breakdown:**")
            for r in data["roles"]:
                lines.append(f"  - {r.get('role', 'Unknown').capitalize()}: {r.get('count', 0)}")

        # Leaderboard / list of employees
        list_keys = ["leaders", "employees", "leaderboard", "Leadersboard", "team"]
        for lk in list_keys:
            if lk in data and isinstance(data[lk], list) and data[lk]:
                lines.append(f"\n**{'Leave Leaderboard' if 'leader' in lk.lower() else 'Employees'}:**")
                for i, emp in enumerate(data[lk], 1):
                    lines.append(_format_employee_item(i, emp))

        # Alerts
        if "alerts" in data and isinstance(data["alerts"], list):
            lines.append("\n**⚠️ Low Leave Alerts:**")
            for emp in data["alerts"]:
                lines.append(f"  - {emp.get('name', 'Unknown')} — only **{emp.get('remaining', '?')} days** remaining")

        # Single employee fields
        for key in ["name", "email", "role", "department"]:
            if key in data:
                lines.append(f"  - {key.capitalize()}: {data[key]}")
        for key in ["used", "remaining", "total"]:
            if key in data:
                lines.append(f"  - Leave {key.capitalize()}: **{data[key]} days**")

        # Generic fallback for unknown keys
        known_keys = set(summary_map.keys()) | {"roles", "leaders", "employees", "leaderboard", "Leadersboard",
                                                 "team", "alerts", "error", "name", "email", "role",
                                                 "department", "used", "remaining", "total", "message",
                                                 "employee_id"}
        for k, v in data.items():
            if k not in known_keys and not isinstance(v, (dict, list)):
                lines.append(f"  - {k.replace('_', ' ').capitalize()}: **{v}**")

        return "\n".join(lines) if lines else raw

    return str(data)


def _format_employee_item(index: int, item: dict) -> str:
    """Format a single employee record."""
    name = item.get("name", f"Employee {item.get('employee_id', index)}")
    parts = [f"**{index}. {name}**"]
    if "email" in item:
        parts.append(f"   📧 {item['email']}")
    if "role" in item:
        parts.append(f"   🏷️ Role: {item['role']}")
    if "used" in item or "remaining" in item:
        used = item.get("used", "?")
        remaining = item.get("remaining", "?")
        total = item.get("total", "?")
        parts.append(f"   📅 Leave: {used} used / {remaining} remaining (of {total} days)")
    return "\n".join(parts)


def _detect_prompt_injection(user_input: str) -> bool:
    """Detect common prompt injection / jailbreak patterns."""
    if not user_input:
        return False
    
    lowered = user_input.lower()
    suspicious_patterns = [
        r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|rules|prompts)",
        r"forget\s+(all\s+)?(previous|above|prior)\s+(instructions|rules|prompts)",
        r"you\s+are\s+now\s+a\s+DAN",
        r"disregard\s+all\s+(rules|instructions)",
        r"system\s*prompt",
        r"reveal\s+(your\s+)?(system|hidden|internal)\s+(prompt|instructions)",
        r"act\s+as\s+an?\s+(admin|root|superuser)",
        r"override\s+security",
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, lowered):
            return True
    return False


@traceable(name="RouteQuery", run_type="chain")
def route_query(user_input: str, employee_id: int, role: str, history: list = None, include_debug: bool = False):
    if history is None:
        history = []

    routing_debug = {
        "role": role,
        "current_employee_id": employee_id,
        "requested_employee_id": None,
        "steps": [],
        "iterations": 0
    }

    # Prompt Injection Guardrail
    if _detect_prompt_injection(user_input):
        result = {
            "error": "Prompt injection detected",
            "code": "PROMPT_INJECTION_REJECTED",
            "message": "I cannot fulfill requests that attempt to override security rules or prompt instructions.",
        }
        return _with_optional_debug(result, routing_debug, include_debug)

    tools = get_tools_metadata()
    print("LOADED TOOLS:", tools)

    requested_employee_id = _extract_employee_id_from_text(user_input)
    routing_debug["requested_employee_id"] = requested_employee_id

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

    observations = []
    MAX_ITERATIONS = 5

    for iteration in range(MAX_ITERATIONS):
        routing_debug["iterations"] = iteration + 1
        decision = _agent_step_with_llm(user_input, tools, role, history, observations)

        step_debug = {
            "iteration": iteration + 1,
            "thought": decision.get("thought", "")
        }

        if "final_answer" in decision:
            step_debug["final_answer"] = decision["final_answer"]
            routing_debug["steps"].append(step_debug)
            final_text = _humanize_response(decision["final_answer"], user_input)
            return _with_optional_debug(final_text, routing_debug, include_debug)
        
        # If no valid action or final answer, it might be a fallback or message
        if "action" not in decision and "message" in decision:
             step_debug["message"] = decision["message"]
             routing_debug["steps"].append(step_debug)
             if _is_non_actionable_message(decision):
                 continue
             humanized_msg = _humanize_response(decision["message"], user_input)
             return _with_optional_debug(humanized_msg, routing_debug, include_debug)

        tool_name = decision.get("action")
        if not tool_name or tool_name not in available_tool_names:
            step_debug["error"] = f"Invalid tool: {tool_name}"
            routing_debug["steps"].append(step_debug)
            observations.append({
                "thought": decision.get("thought", ""),
                "action": tool_name,
                "observation": {"error": f"Tool '{tool_name}' not found. Check AVAILABLE TOOLS."}
            })
            continue

        tool_meta = tool_map.get(tool_name, {})
        tool_parameters = tool_meta.get("parameters", {})

        args = decision.get("action_input", {})
        if not isinstance(args, dict):
            args = {}

        args = _strip_none_values(args)

        if "employee_id" in tool_parameters:
            if role == "employee":
                args["employee_id"] = employee_id
            else:
                args["employee_id"] = requested_employee_id or args.get("employee_id", employee_id)
            args["employee_id"] = _to_int(args.get("employee_id"), employee_id)

        step_debug["action"] = tool_name
        step_debug["action_input"] = dict(args)

        # Loop breaker: prevent the agent from calling the exact same tool with same args twice in a row
        if len(observations) > 0:
             last_obs = observations[-1]
             if last_obs["action"] == tool_name and last_obs["action_input"] == dict(args):
                 warning_msg = {"error": "SYSTEM WARNING: You just made this exact same tool call. DO NOT repeat it! Look at the PREVIOUS STEPS to see the data. If you have the data, output FORMAT 2. If you need a role, use another tool."}
                 step_debug["action_result"] = warning_msg
                 routing_debug["steps"].append(step_debug)
                 observations.append({
                     "thought": decision.get("thought", ""),
                     "action": tool_name,
                     "action_input": dict(args),
                     "observation": warning_msg
                 })
                 continue

        # Check for confirmation requirement
        if tool_meta.get("requires_confirmation", False) and not args.get("__confirmed__", False):
            return {
                "status": "requires_confirmation",
                "tool_name": tool_name,
                "tool_args": args,
                "thought": decision.get("thought", ""),
                "routing_debug": routing_debug
            }

        # Call Tool
        try:
             result = call_tool(
                tool_name,
                args,
                {"employee_id": employee_id, "role": role},
             )
        except Exception as e:
             result = {"error": str(e)}

        step_debug["action_result"] = result
        routing_debug["steps"].append(step_debug)

        observations.append({
            "thought": decision.get("thought", ""),
            "action": tool_name,
            "action_input": dict(args),
            "observation": result
        })

    # If hit loop limit
    final_response = _synthesize_final_after_timeout(user_input, history, observations, role)
    final_response = _polish_response(final_response, user_input)
    return _with_optional_debug(final_response, routing_debug, include_debug)


def call_model(state: AgentState):
    tools = get_tools_metadata()
    tools_for_prompt = _tools_for_prompt(tools, state["role"])
    
    # Track iterations via trace
    current_step = len(state.get("trace", [])) + 1
    
    # Format messages for prompt
    conv_history = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            conv_history += f"User: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            if msg.content:
                conv_history += f"Assistant Thought: {msg.content}\n"
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    conv_history += f"Assistant Action: {tc['name']}({json.dumps(tc['args'])})\n"
        elif isinstance(msg, ToolMessage):
            conv_history += f"Observation: {msg.content}\n"

    prompt = f"""You MUST respond with ONLY a JSON object. No text before or after the JSON. No explanations.

AVAILABLE TOOLS: {json.dumps([t['name'] for t in tools_for_prompt])}

FULL TOOL DETAILS:
{json.dumps(tools_for_prompt, indent=2)}

CONVERSATION:
{conv_history}

Respond with ONE of these exact JSON formats:
Format 1 - Call a tool: {{"thought":"...","action":"tool_name","action_input":{{...}}}}
Format 2 - Give answer: {{"thought":"...","final_answer":"..."}}

IMPORTANT:
- Check CONVERSATION for Observations. If a tool result is there, use it to write final_answer.
- Do NOT repeat a tool if its result is already in CONVERSATION.
- User role: {state['role']}
- Output ONLY the JSON object, starting with {{"""
    llm_output = ask_llm(prompt)
    
    # Parse decision (reusing existing parser)
    parsed = extract_json(llm_output)
    decision = _normalize_decision(parsed)
    
    # Return thought + trace update
    thought = decision.get("thought", "")
    new_trace = state.get("trace", []) + [thought]

    if "action" in decision and decision["action"] != "Invalid response":
        tool_name = decision["action"]
        tool_args = decision.get("action_input", {})
        tool_call_id = f"call_{uuid.uuid4().hex[:8]}"
        
        return {
            "messages": [
                AIMessage(
                    content=thought,
                    tool_calls=[{
                        "name": tool_name,
                        "args": tool_args,
                        "id": tool_call_id
                    }]
                )
            ],
            "trace": new_trace
        }
    
    # If it's a final answer or we're stuck
    final_txt = decision.get("final_answer", decision.get("message"))
    if not final_txt:
         final_txt = llm_output if len(llm_output) < 500 else "I've completed my analysis but couldn't format the final response. Please check previous steps."

    return {
        "messages": [AIMessage(content=final_txt)],
        "trace": new_trace
    }


workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", execute_tools)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("action", "agent")

agent_app = workflow.compile()
