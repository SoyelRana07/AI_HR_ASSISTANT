# AI HR Assistant

AI-powered HR assistant built with FastAPI and Streamlit, using LLM-based tool routing and MCP execution for leave workflows.

## Overview

This project lets employees and managers ask HR leave questions in natural language. The system routes each request to the right backend tool through an LLM router and executes it via an MCP layer.

## Key Features

- Natural language HR queries
- Role-based authentication for employee and manager personas
- Employee data access guardrails
- LLM tool selection with MCP tool execution
- Manager analytics:
	- Team leave summary
	- Manager dashboard
	- Low leave alerts
	- Leave leaderboard
- Routing debug visibility in UI

## Architecture

- Frontend: Streamlit
- API Backend: FastAPI
- Data Layer: SQLAlchemy + PostgreSQL
- LLM Router: Chooses tool from available metadata
- MCP Server: Exposes and executes tools

Flow:

User prompt -> Backend chat endpoint -> LLM router decides tool -> MCP executes tool -> Structured response to UI

## Tech Stack

- Python
- FastAPI
- Streamlit
- SQLAlchemy
- PostgreSQL
- Ollama (local model runtime)

## Project Structure

- backend: API, auth, models, repository, services
- frontend: Streamlit UI
- llm: Router and inference client
- mcp: Server, runtime, registry, tool definitions

## Local Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment

Use backend/.env and set:

- DATABASE_URL (or DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME)
- MCP_MODE
- MCP_SERVER_URL
- MCP_TIMEOUT_SECONDS
- MCP_STRICT_REMOTE
- OLLAMA_URL
- OLLAMA_MODEL
- OLLAMA_TIMEOUT_SECONDS
- BACKEND_CHAT_URL
- ROUTER_RULES_PATH

### 4. Seed database

```powershell
python backend/seed_dummy_data.py
```

### 5. Start services

Terminal 1:

```powershell
python -m uvicorn mcp.server:app --host 127.0.0.1 --port 8003
```

Terminal 2:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 3:

```powershell
cd frontend
streamlit run app.py
```

## Demo Credentials

- Manager: Employee ID 2, Password 0002
- Employee: Employee ID 1, Password 0001

Local dev password rule: zero-padded employee ID unless shared password is configured.

## Example Prompts

Employee:

- show my leave balance
- show my details

Manager:

- show team leave summary
- show manager dashboard
- show low leave alerts
- show leave leaderboard
- show leave balance for employee 4

## Security and Guardrails

- Employees can only access their own leave data
- Manager-only tools are role-protected
- Tool arguments are schema-validated before execution
- Invalid tool calls return structured error payloads

## Debug and Observability

Chat responses include routing debug metadata such as:

- selected_tool
- selected_args
- repair_attempted
- current/requested employee context

This helps verify LLM routing behavior during development.

## Current Status

- Local MVP complete
- Core manager and employee flows validated
- UI polished for portfolio/demo presentation
- Deployment intentionally deferred

## Roadmap

- Password hashing and stronger auth hardening
- Rate limiting and quota protection
- Automated tests for routing and authorization
- Optional cloud deployment
