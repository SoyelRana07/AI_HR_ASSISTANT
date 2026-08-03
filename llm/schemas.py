import json
from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, Optional, Union


class AgentAction(BaseModel):
    thought: str = Field(description="Internal reasoning for the next step")
    action: str = Field(description="Name of the tool to call")
    action_input: Dict = Field(default_factory=dict, description="Arguments for the tool")


class AgentFinish(BaseModel):
    thought: str = Field(description="Internal reasoning for finishing")
    final_answer: Any = Field(description="Final response to the user — string or structured data")

    @field_validator("final_answer", mode="before")
    @classmethod
    def coerce_to_string(cls, v):
        """If the LLM returns a dict/list as final_answer, serialize it to a
        nicely formatted JSON string so the response is always a string."""
        if isinstance(v, (dict, list)):
            return json.dumps(v, indent=2)
        return str(v)


class AgentStep(BaseModel):
    decision: Union[AgentAction, AgentFinish]
