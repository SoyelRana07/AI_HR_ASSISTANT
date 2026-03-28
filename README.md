AI HR Assistant
An AI-powered HR assistant built with FastAPI and Streamlit, using LLM-based tool routing and MCP execution for leave management workflows.

Overview
This project lets employees and managers ask HR leave questions in natural language.
The system routes each request to the right backend tool through an LLM router and executes it via an MCP layer.

Key Features
Natural language HR queries
Role-based authentication (employee and manager)
Employee data access guardrails
LLM tool selection with MCP tool execution
Manager analytics:
Team leave summary
Leave dashboard
Low leave alerts
Leaderboard
Routing debug visibility in UI
Architecture
Frontend: Streamlit
API Backend: FastAPI
Data Layer: SQLAlchemy + PostgreSQL
LLM Router: Chooses tool from available tool metadata
MCP Server: Exposes tools and executes selected actions
Flow:
User prompt -> Backend chat endpoint -> LLM router decides tool -> MCP tool execution -> Structured response to UI

Tech Stack
Python
FastAPI
Streamlit
SQLAlchemy
PostgreSQL
Ollama (local model runtime)
Project Structure
backend: API, auth, DB models, repository/services
frontend: Streamlit interface
llm: Router and LLM engine
mcp: MCP server, runtime, tool registry, tool implementations
Local Setup
1. Create and activate virtual environment
Windows PowerShell:
python -m venv .venv
Activate.ps1

2. Install dependencies
pip install -r requirements.txt

3. Configure environment
Create .env (or update existing) with:

DATABASE_URL or DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME
MCP_MODE
MCP_SERVER_URL
MCP_TIMEOUT_SECONDS
MCP_STRICT_REMOTE
OLLAMA_URL
OLLAMA_MODEL
OLLAMA_TIMEOUT_SECONDS
BACKEND_CHAT_URL
ROUTER_RULES_PATH


4. Seed database
python seed_dummy_data.py

5. Start services
Terminal 1:
python -m uvicorn mcp.server:app --host 127.0.0.1 --port 8003

Terminal 2:
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

Terminal 3:
cd frontend
streamlit run app.py

Login Credentials (Demo Seed Data)
Manager:

Employee ID: 2

Password: 0002

Employee example:

Employee ID: 1

Password: 0001

Password rule in local dev:
Zero-padded employee ID unless shared password is configured.

Example Prompts
Employee:

Show my leave balance
Show my details
Manager:

Show team leave summary
Show manager dashboard
Show low leave alerts
Show leave leaderboard
Show leave balance for employee 4
Security and Guardrails
Employees can only access their own leave data
Manager-only tools are role-protected
Tool arguments are schema-validated before execution
Invalid tool calls return structured error responses


Debug and Observability
The chat response includes routing debug metadata, such as:
selected_tool
selected_args
repair_attempted
current/requested employee context
Useful for verifying LLM routing behavior during development.

Current Status
Local MVP complete
Core manager and employee flows validated
UI polished for portfolio/demo presentation
Deployment intentionally deferred
Roadmap
Password hashing and stronger auth hardening
Rate limiting and quota protection
Automated tests for routing and authorization
Optional cloud deployment
