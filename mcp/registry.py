TOOL_REGISTRY = {}

def register_tool(
    name,
    description,
    parameters,
    input_model=None,
    required_role=None,
    requires_confirmation=False,
):
    def decorator(func):
        TOOL_REGISTRY[name] = {
            "function": func,
            "description": description,
            "parameters": parameters,
            "input_model": input_model,
            "required_role": required_role,
            "requires_confirmation": requires_confirmation,
        }
        return func
    return decorator



def _ensure_tools_loaded():
    if not TOOL_REGISTRY:
        try:
            import mcp.tools.leave_tools  # noqa: F401
        except Exception:
            pass


def get_tools_metadata():
    _ensure_tools_loaded()
    tools = []

    for name, data in TOOL_REGISTRY.items():
        tool_item = {
            "name": name,
            "description": data["description"],
            "parameters": data["parameters"],
            "required_role": data.get("required_role"),
            "requires_confirmation": data.get("requires_confirmation", False),
        }

        input_model = data.get("input_model")
        if input_model is not None:
            tool_item["input_schema"] = input_model.model_json_schema()

        tools.append(tool_item)

    return tools