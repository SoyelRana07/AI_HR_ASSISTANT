import React, { useState } from 'react';
import { Bot, UserCheck, ShieldAlert } from 'lucide-react';

export default function LoginPage({ onLoginSuccess, initialError = '' }) {
  const [employeeId, setEmployeeId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(initialError);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (idToUse, passToUse) => {
    const targetId = idToUse || employeeId;
    const targetPass = passToUse || password;

    if (!targetId || !targetPass) {
      setError('Please enter Employee ID and Password.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: parseInt(targetId, 10),
          password: targetPass,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      onLoginSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const selectDemoUser = (id, pass) => {
    setEmployeeId(id);
    setPassword(pass);
    handleLogin(id, pass);
  };

  return (
    <div className="login-overlay">
      <div className="login-card">
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div className="brand-icon" style={{ margin: '0 auto 1rem auto', width: '48px', height: '48px' }}>
            <Bot size={28} color="white" />
          </div>
          <h2>AI HR Assistant</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Bcrypt Authenticated Portal
          </p>
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--danger)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#fca5a5' }}>
            <ShieldAlert size={18} /> {error}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Employee ID</label>
            <input
              type="number"
              className="chat-input"
              style={{ width: '100%', marginTop: '0.25rem' }}
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              placeholder="e.g. 1 (Employee) or 2 (Manager)"
            />
          </div>

          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Password</label>
            <input
              type="password"
              className="chat-input"
              style={{ width: '100%', marginTop: '0.25rem' }}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="e.g. 0001 or 0002"
            />
          </div>

          <button
            onClick={() => handleLogin()}
            disabled={loading}
            className="new-chat-btn"
            style={{ width: '100%', marginTop: '0.5rem' }}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </div>

        <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            Quick Demo Login:
          </p>
          <div className="demo-pills">
            <button className="demo-pill" onClick={() => selectDemoUser('1', '0001')}>
              👤 Employee (ID 1)
            </button>
            <button className="demo-pill" onClick={() => selectDemoUser('2', '0002')}>
              👔 Manager (ID 2)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
