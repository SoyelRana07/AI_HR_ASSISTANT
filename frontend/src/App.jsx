import React, { useState, useEffect } from 'react';
import { Bot, Send, LogOut, Plus, ShieldCheck, Terminal, AlertTriangle } from 'lucide-react';
import LoginPage from './LoginPage';

export default function App() {
  const [authData, setAuthData] = useState(() => {
    const saved = localStorage.getItem('hr_auth');
    return saved ? JSON.parse(saved) : null;
  });

  const [sessionId, setSessionId] = useState(() => `session_${Date.now()}`);
  const [messages, setMessages] = useState([]);
  const [inputMsg, setInputMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState(null);
  const [showDebug, setShowDebug] = useState(false);

  useEffect(() => {
    if (authData) {
      localStorage.setItem('hr_auth', JSON.stringify(authData));
      loadConversationHistory(sessionId);
    } else {
      localStorage.removeItem('hr_auth');
    }
  }, [authData, sessionId]);

  const loadConversationHistory = async (sessId) => {
    if (!authData) return;
    try {
      const res = await fetch(`http://localhost:8000/conversations/${sessId}`, {
        headers: { Authorization: `Bearer ${authData.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        if (data.messages) {
          setMessages(
            data.messages.map((m) => ({
              sender: m.role,
              text: m.content,
            }))
          );
        }
      }
    } catch (e) {
      console.error('Error loading history:', e);
    }
  };

  const [pendingConfirmation, setPendingConfirmation] = useState(null);

  const handleSendMessage = async (textToSend) => {
    const msg = textToSend || inputMsg;
    if (!msg.trim() || loading) return;

    const userMessage = { sender: 'user', text: msg };
    setMessages((prev) => [...prev, userMessage]);
    if (!textToSend) setInputMsg('');
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authData.access_token}`,
        },
        body: JSON.stringify({
          message: msg,
          session_id: sessionId,
        }),
      });

      const data = await res.json();
      if (data.routing_debug) setDebugInfo(data.routing_debug);

      if (data.status === 'requires_confirmation') {
        setPendingConfirmation({
          tool_name: data.tool_name,
          tool_args: data.tool_args,
          thought: data.thought,
        });
      } else {
        const botText = typeof data.response === 'string'
          ? data.response
          : JSON.stringify(data.response, null, 2);
        setMessages((prev) => [...prev, { sender: 'assistant', text: botText }]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: 'assistant', text: `⚠️ Error communicating with server: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmToolExecution = async () => {
    if (!pendingConfirmation) return;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/execute_tool', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authData.access_token}`,
        },
        body: JSON.stringify({
          tool_name: pendingConfirmation.tool_name,
          tool_args: pendingConfirmation.tool_args,
        }),
      });

      const data = await res.json();
      const botText = typeof data.response === 'string'
        ? data.response
        : JSON.stringify(data.response, null, 2);

      setMessages((prev) => [...prev, { sender: 'assistant', text: botText }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: 'assistant', text: `⚠️ Error executing tool: ${err.message}` },
      ]);
    } finally {
      setPendingConfirmation(null);
      setLoading(false);
    }
  };

  const handleCancelToolExecution = () => {
    setPendingConfirmation(null);
    setMessages((prev) => [...prev, { sender: 'assistant', text: 'Action cancelled by user.' }]);
  };

  const handleNewChat = () => {
    const newSess = `session_${Date.now()}`;
    setSessionId(newSess);
    setMessages([]);
    setDebugInfo(null);
  };

  const handleLogout = () => {
    setAuthData(null);
    setMessages([]);
  };

  if (!authData) {
    return <LoginPage onLoginSuccess={(data) => setAuthData(data)} />;
  }

  const isManager = authData.user.role === 'manager';

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-icon">
            <Bot color="white" size={22} />
          </div>
          <div>
            <h3 style={{ fontSize: '1rem' }}>AI HR Assistant</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              MCP + Ollama Router
            </span>
          </div>
        </div>

        <button onClick={handleNewChat} className="new-chat-btn">
          <Plus size={18} /> New Conversation
        </button>

        <div style={{ flex: 1, overflowY: 'auto', margin: '0.5rem 0' }}>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            Quick Prompts:
          </p>

          <button
            className="demo-pill"
            style={{ width: '100%', marginBottom: '0.5rem', textAlign: 'left' }}
            onClick={() => handleSendMessage('show my leave balance')}
          >
            💬 Show my leave balance
          </button>

          {isManager && (
            <>
              <button
                className="demo-pill"
                style={{ width: '100%', marginBottom: '0.5rem', textAlign: 'left' }}
                onClick={() => handleSendMessage('show team leave summary')}
              >
                📊 Team Leave Summary
              </button>
              <button
                className="demo-pill"
                style={{ width: '100%', marginBottom: '0.5rem', textAlign: 'left' }}
                onClick={() => handleSendMessage('show low leave alerts')}
              >
                ⚠️ Low Leave Alerts
              </button>
              <button
                className="demo-pill"
                style={{ width: '100%', marginBottom: '0.5rem', textAlign: 'left' }}
                onClick={() => handleSendMessage('show leave leaderboard')}
              >
                🏆 Leave Leaderboard
              </button>
            </>
          )}
        </div>

        <div className="user-profile-card">
          <div>
            <div style={{ fontWeight: '600', fontSize: '0.85rem' }}>{authData.user.name}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <ShieldCheck size={12} color="var(--success)" /> {authData.user.role.toUpperCase()} (ID: {authData.user.employee_id})
            </div>
          </div>
          <button onClick={handleLogout} className="logout-btn" title="Sign Out">
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      {/* Main Chat Canvas */}
      <main className="main-canvas">
        <header className="chat-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontWeight: '600' }}>HR Assistant Session</span>
            <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              {sessionId}
            </span>
          </div>

          <button
            onClick={() => setShowDebug(!showDebug)}
            style={{ background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-muted)', padding: '0.4rem 0.75rem', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
          >
            <Terminal size={16} /> Debug Router
          </button>
        </header>

        <div className="chat-thread">
          {messages.length === 0 ? (
            <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-muted)', maxWidth: '400px' }}>
              <Bot size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
              <h3>How can I help you today?</h3>
              <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
                Ask HR leave questions in natural language. Powered by FastAPI, Model Context Protocol (MCP), and Ollama.
              </p>
            </div>
          ) : (
            messages.map((m, idx) => (
              <div key={idx} className={`message-bubble ${m.sender}`}>
                <div style={{ whiteSpace: 'pre-wrap' }}>{m.text}</div>
              </div>
            ))
          )}

          {pendingConfirmation && (
            <div className="message-bubble assistant" style={{ border: '1px solid var(--accent-purple)', background: '#1e1b4b' }}>
              <div style={{ fontWeight: 'bold', color: '#c084fc', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                ⚠️ Confirmation Required
              </div>
              <p style={{ fontSize: '0.85rem', marginBottom: '0.75rem' }}>
                The assistant wants to execute <strong>{pendingConfirmation.tool_name}</strong>:
              </p>
              <pre style={{ background: '#090d16', padding: '0.5rem', borderRadius: '6px', fontSize: '0.8rem', color: '#a7f3d0', marginBottom: '0.75rem' }}>
                {JSON.stringify(pendingConfirmation.tool_args, null, 2)}
              </pre>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={handleConfirmToolExecution}
                  style={{ background: 'var(--success)', color: 'white', border: 'none', padding: '0.4rem 0.85rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '600', fontSize: '0.85rem' }}
                >
                  Confirm & Submit
                </button>
                <button
                  onClick={handleCancelToolExecution}
                  style={{ background: 'var(--danger)', color: 'white', border: 'none', padding: '0.4rem 0.85rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '600', fontSize: '0.85rem' }}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {loading && !pendingConfirmation && (
            <div className="message-bubble assistant" style={{ opacity: 0.7 }}>
              🤖 Routing query through LLM & MCP tool...
            </div>
          )}
        </div>

        {/* Debug Drawer */}
        {showDebug && debugInfo && (
          <div style={{ background: '#090d16', borderTop: '1px solid var(--border-color)', padding: '1rem', maxHeight: '180px', overflowY: 'auto', fontSize: '0.8rem', fontFamily: 'monospace' }}>
            <div style={{ color: 'var(--accent-purple)', fontWeight: 'bold', marginBottom: '0.25rem' }}>
              🔍 Routing Debug Metadata:
            </div>
            <pre>{JSON.stringify(debugInfo, null, 2)}</pre>
          </div>
        )}

        <div className="chat-input-area">
          <input
            type="text"
            className="chat-input"
            placeholder="Type your HR question (e.g. 'show my leave balance')..."
            value={inputMsg}
            onChange={(e) => setInputMsg(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
          />
          <button onClick={() => handleSendMessage()} className="send-btn" disabled={loading}>
            <Send size={18} />
          </button>
        </div>
      </main>
    </div>
  );
}
