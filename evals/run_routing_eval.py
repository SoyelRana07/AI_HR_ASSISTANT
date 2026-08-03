import os
import sys
import argparse

# Ensure root workspace directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), "..", "backend", ".env")
load_dotenv(dotenv_path=env_path)

from llm.router import route_query
import mcp.tools.leave_tools


def run_eval(enable_langsmith: bool = False):
    if enable_langsmith:
        print("[LangSmith] Tracing ENABLED! Project:", os.getenv("LANGCHAIN_PROJECT"))
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    
    print("\n--- Running Test Query 1: Employee Leave Balance ---")
    res1 = route_query("show my leave balance", employee_id=1, role="employee", include_debug=True)
    out1 = str(res1.get("data", res1) if isinstance(res1, dict) else res1)
    print("Response 1:", out1.encode('ascii', 'replace').decode('ascii'))

    print("\n--- Running Test Query 2: Manager Team Summary ---")
    res2 = route_query("show team leave summary", employee_id=2, role="manager", include_debug=True)
    out2 = str(res2.get("data", res2) if isinstance(res2, dict) else res2)
    print("Response 2:", out2.encode('ascii', 'replace').decode('ascii'))

    print("\n[SUCCESS] Evaluation run complete! Check your LangSmith dashboard at https://smith.langchain.com")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLM Routing Evals with optional LangSmith tracing.")
    parser.add_argument("--langsmith", action="store_true", help="Enable LangSmith tracing V2")
    args = parser.parse_args()

    run_eval(enable_langsmith=args.langsmith)
