# frontend/app.py

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import requests
from env_config import get_required_env, load_project_env


load_project_env(__file__)
required = get_required_env(["BACKEND_CHAT_URL", "MCP_SERVER_URL"])
BACKEND_CHAT_URL = required["BACKEND_CHAT_URL"]
MCP_SERVER_URL = required["MCP_SERVER_URL"]
BACKEND_BASE_URL = BACKEND_CHAT_URL[:-5] if BACKEND_CHAT_URL.endswith("/chat") else BACKEND_CHAT_URL

if "auth_token" not in st.session_state:
    st.session_state.auth_token = ""
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "messages" not in st.session_state:
    st.session_state.messages = []


def _auth_headers():
    token = st.session_state.auth_token
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}

st.set_page_config(
    page_title="AI HR Assistant",
    page_icon=":office:",
    layout="wide",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Fraunces:opsz,wght@9..144,500;9..144,700&display=swap');

:root {
    --bg-1: #f8f5ef;
    --bg-2: #f1ece2;
    --bg-3: #fefcf8;
    --card: rgba(255, 255, 255, 0.92);
    --text: #1b1a18;
    --muted: #57524a;
    --accent: #cc4f2b;
    --accent-2: #2f7d7a;
    --accent-3: #2e5b9a;
    --accent-soft: rgba(204, 79, 43, 0.10);
    --warning: #b86a0d;
    --border: rgba(27, 26, 24, 0.14);
    --control-bg: #fffdf9;
    --control-border: #d7c9b7;
    --control-text: #2b2925;
    --button-text: #ffffff;
}

.stApp {
    background:
        radial-gradient(880px 460px at -10% -12%, rgba(204,79,43,0.23), transparent 68%),
        radial-gradient(840px 540px at 110% -8%, rgba(47,125,122,0.22), transparent 66%),
        linear-gradient(145deg, var(--bg-1), var(--bg-2) 46%, var(--bg-3));
    color: var(--text);
    font-family: 'Sora', sans-serif;
}

.stApp::before {
    content: "";
    position: fixed;
    inset: auto -18% -36% auto;
    width: 460px;
    height: 460px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(46,91,154,0.20), rgba(46,91,154,0.0) 70%);
    pointer-events: none;
    z-index: 0;
    animation: floatOrb 14s ease-in-out infinite;
}

@keyframes floatOrb {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(-22px, -14px); }
}

h1, h2, h3, p, label, span, div {
    font-family: 'Sora', sans-serif !important;
}

[data-testid="stMetricValue"], [data-testid="stMetricLabel"], .mono {
    font-family: 'JetBrains Mono', monospace !important;
    color: var(--text) !important;
}

h1, h2, h3 {
    color: var(--text) !important;
}

.hero {
    padding: 1.35rem 1.4rem;
    border-radius: 24px;
    background:
        linear-gradient(118deg, rgba(255,255,255,0.94), rgba(253,247,239,0.92)),
        repeating-linear-gradient(45deg, rgba(46,91,154,0.04) 0 8px, transparent 8px 16px);
    border: 1px solid var(--border);
    box-shadow: 0 20px 44px rgba(34, 28, 18, 0.16);
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
}

.hero::after {
    content: "AI SYSTEMS PORTFOLIO";
    position: absolute;
    right: 16px;
    top: 12px;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.70rem;
    letter-spacing: 0.10rem;
    color: rgba(27,26,24,0.45);
}

.hero-title {
    font-family: 'Fraunces', serif !important;
    font-size: 2.25rem;
    font-weight: 700;
    line-height: 1.0;
    letter-spacing: -0.02rem;
    margin: 0;
    color: var(--text);
}

.hero-sub {
    color: var(--muted);
    margin-top: 0.65rem;
    font-size: 1.03rem;
    max-width: 880px;
}

.status-chip {
    display: inline-block;
    margin-top: 0.7rem;
    margin-right: 0.45rem;
    padding: 0.42rem 0.8rem;
    border-radius: 999px;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: 0.84rem;
    border: 1px solid rgba(10, 102, 194, 0.34);
    font-weight: 600;
}

.status-chip strong {
    font-family: 'JetBrains Mono', monospace !important;
}

.panel {
    border-radius: 18px;
    padding: 1.08rem;
    background: var(--card);
    border: 1px solid var(--border);
    box-shadow: 0 14px 30px rgba(40, 33, 21, 0.11);
}

.response-box {
    border-left: 4px solid var(--accent-3);
    background: linear-gradient(145deg, rgba(247,251,255,0.96), rgba(255,252,246,0.95));
    border-radius: 12px;
    padding: 0.75rem 0.9rem;
}

.showcase-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.65rem;
    margin-bottom: 0.95rem;
}

.showcase-card {
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 0.75rem 0.8rem;
    background: linear-gradient(180deg, rgba(255,255,255,0.85), rgba(248,241,230,0.83));
}

.showcase-kicker {
    font-size: 0.72rem;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.25rem;
}

.showcase-main {
    font-weight: 700;
    color: var(--text);
    line-height: 1.2;
}

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.78);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.4rem 0.6rem;
}

label, [data-testid="stWidgetLabel"] p {
    color: var(--text) !important;
    font-weight: 600 !important;
}

/* Inputs */
[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
textarea {
    background: var(--control-bg) !important;
    border: 1px solid var(--control-border) !important;
    border-radius: 10px !important;
}

input, textarea {
    color: var(--control-text) !important;
    -webkit-text-fill-color: var(--control-text) !important;
    font-weight: 500 !important;
}

[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: var(--control-text) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(130deg, var(--accent), #d06445 52%, var(--accent-2));
    color: var(--button-text) !important;
    border: 1px solid rgba(70, 35, 17, 0.30);
    border-radius: 12px;
    font-weight: 700;
    letter-spacing: 0.24px;
    box-shadow: 0 10px 24px rgba(92, 44, 22, 0.28);
    transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease, opacity 120ms ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    filter: saturate(1.08);
    box-shadow: 0 14px 30px rgba(92, 44, 22, 0.31);
}

.stButton > button:active {
    transform: translateY(0);
}

.stButton > button:focus-visible {
    outline: 3px solid rgba(204, 79, 43, 0.35);
    outline-offset: 1px;
}

/* Chat UI fixes */
[data-testid="stChatMessage"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 0.8rem !important;
    box-shadow: 0 6px 16px rgba(40, 33, 21, 0.08) !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] > p {
    color: var(--text) !important;
    font-weight: 500;
}

/* JSON block readability */
[data-testid="stJson"] {
    background: #18273a !important;
    border: 1px solid rgba(116, 190, 219, 0.31);
    border-radius: 10px;
}

[data-testid="stJson"] * {
    color: #d9e8ff !important;
}

@media (max-width: 960px) {
    .hero-title {
        font-size: 1.9rem;
    }

    .showcase-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 620px) {
    .showcase-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<section class="hero">
    <p class="hero-title">AI HR Control Room</p>
    <p class="hero-sub">Production-style AI assistant prototype with LLM-driven tool routing, MCP execution, role-based access controls, and recruiter-friendly observability traces.</p>
    <span class="status-chip"><strong>API</strong> <span class="mono">{BACKEND_CHAT_URL}</span></span>
    <span class="status-chip"><strong>MCP</strong> <span class="mono">{MCP_SERVER_URL}</span></span>
</section>

<section class="showcase-grid">
    <div class="showcase-card">
        <div class="showcase-kicker">Architecture</div>
        <div class="showcase-main">LLM Router + MCP Tool Runtime</div>
    </div>
    <div class="showcase-card">
        <div class="showcase-kicker">Security</div>
        <div class="showcase-main">Role Guardrails for Employee Scope</div>
    </div>
    <div class="showcase-card">
        <div class="showcase-kicker">Visibility</div>
        <div class="showcase-main">Selected Tool & Args Debug Trail</div>
    </div>
    <div class="showcase-card">
        <div class="showcase-kicker">Recruiter Signal</div>
        <div class="showcase-main">End-to-End AI Product Engineering</div>
    </div>
</section>
""",
    unsafe_allow_html=True,
)

left, right = st.columns([1.05, 1], gap="large")

with left:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Login")
    login_employee_id = st.number_input("Employee ID", min_value=1, step=1, value=1)
    login_password = st.text_input("Password", type="password")

    login_col, logout_col = st.columns(2)
    with login_col:
        login_clicked = st.button("Login", use_container_width=True)
    with logout_col:
        logout_clicked = st.button("Logout", use_container_width=True)

    if login_clicked:
        try:
            login_res = requests.post(
                f"{BACKEND_BASE_URL}/auth/login",
                json={"employee_id": int(login_employee_id), "password": login_password},
                timeout=15,
            )
            if login_res.status_code == 200:
                login_payload = login_res.json()
                st.session_state.auth_token = login_payload.get("access_token", "")
                st.session_state.current_user = login_payload.get("user")
                st.success("Login successful")
            else:
                try:
                    detail = login_res.json().get("detail", "Login failed")
                except ValueError:
                    detail = "Login failed"
                st.error(detail)
        except requests.RequestException as exc:
            st.error(f"Login request failed: {exc}")

    if logout_clicked:
        st.session_state.auth_token = ""
        st.session_state.current_user = None
        st.info("Logged out")

    current_user = st.session_state.current_user

    if current_user:
        st.caption(
            f"Logged in as {current_user.get('name', 'Unknown')} "
            f"(ID: {current_user.get('employee_id', '?')}, role: {current_user.get('role', '?')})"
        )
    else:
        st.caption("Not logged in. Default development password is your zero-padded employee ID (for example: 0001).")

    st.subheader("Session")

    active_role = current_user.get("role", "employee") if current_user else "employee"

    presets = {
        "employee": [
            "show my leave balance",
            "show my details",
        ],
        "manager": [
            "show manager dashboard",
            "show team leave summary",
            "show low leave alerts",
            "show leave leaderboard",
            "show employee directory",
            "show role breakdown",
        ],
    }
    quick = st.selectbox("Quick Prompt", options=["(custom)"] + presets.get(active_role, presets["employee"]))

    default_prompt = "" if quick == "(custom)" else quick
    msg = st.text_area("Message", value=default_prompt, height=120)

    send = st.button("Run Query", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Conversation")

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            if isinstance(m["content"], dict):
                st.json(m["content"])
            else:
                st.markdown(m["content"])
            if m.get("routing_debug"):
                with st.expander("Routing Debug", expanded=False):
                    st.json(m["routing_debug"])

    if send:
        if not st.session_state.auth_token:
            st.warning("Please login first.")
        elif not msg.strip():
            st.warning("Enter a message before running the query.")
        else:
            st.session_state.messages.append({"role": "user", "content": msg})
            
            with st.chat_message("user"):
                st.markdown(msg)
            
            start = time.perf_counter()
            try:
                history_for_api = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                    if isinstance(m["content"], str)
                ]
                
                with st.spinner("Thinking..."):
                    res = requests.post(
                        BACKEND_CHAT_URL,
                        json={"message": msg, "history": history_for_api},
                        headers=_auth_headers(),
                        timeout=30,
                    )
                    res.raise_for_status()
                
                latency_ms = int((time.perf_counter() - start) * 1000)
                payload = res.json()
                response_body = payload.get("response", payload)
                routing_debug = payload.get("routing_debug", {})

                warning_text = None
                if isinstance(response_body, dict) and response_body.get("code") == "FORBIDDEN_EMPLOYEE_SCOPE":
                    details = response_body.get("details", {})
                    warning_text = response_body.get("message", "Access denied.")
                    if isinstance(details, dict) and "requested_employee_id" in details:
                        warning_text += f" Requested: {details['requested_employee_id']}, Yours: {details['current_employee_id']}."

                st.session_state.messages.append({"role": "assistant", "content": response_body, "routing_debug": routing_debug})
                
                with st.chat_message("assistant"):
                    if warning_text:
                        st.warning(warning_text)
                    if isinstance(response_body, dict):
                        st.json(response_body)
                    else:
                        st.markdown(response_body)
                    
                    st.caption(f"Round-trip: {latency_ms} ms")
                    if routing_debug:
                        with st.expander("Routing Debug", expanded=False):
                            st.json(routing_debug)

            except requests.RequestException as exc:
                st.error(f"Request failed: {exc}")
                st.session_state.messages.pop()

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='panel'>", unsafe_allow_html=True)
st.subheader("MCP Admin")

admin_col1, admin_col2, admin_col3 = st.columns(3)

with admin_col1:
    refresh_tools = st.button("Refresh MCP Tool Catalog", use_container_width=True)
with admin_col2:
    refresh_health = st.button("Check Backend Config Health", use_container_width=True)
with admin_col3:
    run_system_check = st.button("Run Full System Check", use_container_width=True)


def _backend_health_url_from_chat_url(chat_url: str):
    return chat_url[:-5] + "/health/config" if chat_url.endswith("/chat") else chat_url + "/health/config"

if refresh_tools:
    try:
        tools_res = requests.get(f"{MCP_SERVER_URL}/tools", timeout=15)
        tools_res.raise_for_status()
        tools_data = tools_res.json()
        st.metric("Registered MCP Tools", len(tools_data))
        st.json(tools_data)
    except requests.RequestException as exc:
        st.error(f"Failed to fetch MCP tools: {exc}")

if refresh_health:
    try:
        health_url = _backend_health_url_from_chat_url(BACKEND_CHAT_URL)
        health_res = requests.get(health_url, timeout=15)
        health_res.raise_for_status()
        health_data = health_res.json()
        status = health_data.get("status", "unknown")
        if status == "ok":
            st.success("Backend config health: OK")
        else:
            st.warning("Backend config health: missing configuration")
        st.json(health_data)
    except requests.RequestException as exc:
        st.error(f"Failed to fetch backend config health: {exc}")

if run_system_check:
    check_col1, check_col2, check_col3 = st.columns(3)

    mcp_ok = False
    tools_ok = False
    backend_ok = False

    try:
        mcp_health_res = requests.get(f"{MCP_SERVER_URL}/health", timeout=15)
        mcp_health_res.raise_for_status()
        mcp_health_data = mcp_health_res.json()
        mcp_ok = mcp_health_data.get("status") == "ok"
    except requests.RequestException as exc:
        mcp_health_data = {"error": str(exc)}

    try:
        tools_res = requests.get(f"{MCP_SERVER_URL}/tools", timeout=15)
        tools_res.raise_for_status()
        tools_data = tools_res.json()
        tools_ok = isinstance(tools_data, list)
    except requests.RequestException as exc:
        tools_data = {"error": str(exc)}

    try:
        backend_health_res = requests.get(_backend_health_url_from_chat_url(BACKEND_CHAT_URL), timeout=15)
        backend_health_res.raise_for_status()
        backend_health_data = backend_health_res.json()
        backend_ok = backend_health_data.get("status") == "ok"
    except requests.RequestException as exc:
        backend_health_data = {"error": str(exc)}

    with check_col1:
        st.metric("MCP Health", "OK" if mcp_ok else "FAIL")
    with check_col2:
        tool_count = len(tools_data) if isinstance(tools_data, list) else 0
        st.metric("MCP Tool Count", tool_count)
    with check_col3:
        st.metric("Backend Config", "OK" if backend_ok else "FAIL")

    st.caption("System check details")
    st.json(
        {
            "mcp_health": mcp_health_data,
            "mcp_tools": tools_data,
            "backend_config_health": backend_health_data,
        }
    )

st.markdown("</div>", unsafe_allow_html=True)