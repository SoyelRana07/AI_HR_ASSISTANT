import time
from typing import Any, Dict
from pydantic import ValidationError
from mcp.registry import TOOL_REGISTRY, _ensure_tools_loaded
from backend.repository.audit_repo import log_audit_event


class ToolCallError(Exception):
    def __init__(self, code: str, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_payload(self):
        return {
            "ok": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


def execute_tool(name: str, args: Dict[str, Any], context: Dict[str, Any]):
    _ensure_tools_loaded()
    tool = TOOL_REGISTRY.get(name)

    emp_id = context.get("employee_id")
    caller_role = context.get("role")
    start_t = time.perf_counter()

    if not tool:
        log_audit_event(
            event_type="TOOL_EXECUTION",
            status="NOT_FOUND",
            employee_id=emp_id,
            role=caller_role,
            tool_name=name,
            parameters=args,
            execution_time_ms=0,
            details={"error": "Tool not found"},
        )
        raise ToolCallError("TOOL_NOT_FOUND", f"Tool '{name}' not found")

    required_role = tool.get("required_role")

    if required_role and caller_role != required_role:
        log_audit_event(
            event_type="SECURITY_REJECTION",
            status="FORBIDDEN",
            employee_id=emp_id,
            role=caller_role,
            tool_name=name,
            parameters=args,
            execution_time_ms=0,
            details={"required_role": required_role, "caller_role": caller_role},
        )
        raise ToolCallError(
            "FORBIDDEN_TOOL",
            f"Tool '{name}' requires role '{required_role}'",
            {"required_role": required_role, "caller_role": caller_role},
        )

    # Filter out internal metadata flags (e.g. __confirmed__) before validation
    clean_args = {k: v for k, v in args.items() if not k.startswith("__")}

    input_model = tool.get("input_model")
    if input_model is not None:
        try:
            validated_args = input_model.model_validate(clean_args)
            clean_args = validated_args.model_dump()
        except ValidationError as exc:
            log_audit_event(
                event_type="TOOL_EXECUTION",
                status="INVALID_ARGUMENTS",
                employee_id=emp_id,
                role=caller_role,
                tool_name=name,
                parameters=args,
                execution_time_ms=0,
                details={"errors": exc.errors()},
            )
            raise ToolCallError(
                "INVALID_ARGUMENTS",
                f"Invalid arguments for tool '{name}'",
                {"validation_errors": exc.errors()},
            )

    try:
        result = tool["function"](clean_args, context)
        duration_ms = int((time.perf_counter() - start_t) * 1000)
        log_audit_event(
            event_type="TOOL_EXECUTION",
            status="SUCCESS",
            employee_id=emp_id,
            role=caller_role,
            tool_name=name,
            parameters=clean_args,
            execution_time_ms=duration_ms,
        )
        return result
    except ToolCallError:
        raise
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_t) * 1000)
        log_audit_event(
            event_type="TOOL_EXECUTION",
            status="FAILED",
            employee_id=emp_id,
            role=caller_role,
            tool_name=name,
            parameters=clean_args,
            execution_time_ms=duration_ms,
            details={"reason": str(exc)},
        )
        raise ToolCallError(
            "TOOL_EXECUTION_FAILED",
            f"Tool '{name}' execution failed",
            {"reason": str(exc)},
        )

