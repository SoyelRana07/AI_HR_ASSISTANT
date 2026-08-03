import os
import sys
import pytest

# Ensure root workspace directory is in python path when script is run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm.router import route_query


def test_langsmith_tracing_clean_execution():
    """Verify that route_query annotated with LangSmith @traceable executes cleanly."""
    res = route_query(
        user_input="show my leave balance",
        employee_id=1,
        role="employee",
        include_debug=True
    )
    
    assert res is not None
    data = res.get("data", res)
    assert data is not None
