from typing import Any, Dict

from pydantic import ValidationError

from mcp.registry import TOOL_REGISTRY


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
    tool = TOOL_REGISTRY.get(name)

    if not tool:
        raise ToolCallError("TOOL_NOT_FOUND", f"Tool '{name}' not found")

    required_role = tool.get("required_role")
    caller_role = context.get("role")

    if required_role and caller_role != required_role:
        raise ToolCallError(
            "FORBIDDEN_TOOL",
            f"Tool '{name}' requires role '{required_role}'",
            {"required_role": required_role, "caller_role": caller_role},
        )

    input_model = tool.get("input_model")
    if input_model is not None:
        try:
            validated_args = input_model.model_validate(args)
            args = validated_args.model_dump()
        except ValidationError as exc:
            raise ToolCallError(
                "INVALID_ARGUMENTS",
                f"Invalid arguments for tool '{name}'",
                {"validation_errors": exc.errors()},
            )

    try:
        return tool["function"](args, context)
    except ToolCallError:
        raise
    except Exception as exc:
        raise ToolCallError(
            "TOOL_EXECUTION_FAILED",
            f"Tool '{name}' execution failed",
            {"reason": str(exc)},
        )
