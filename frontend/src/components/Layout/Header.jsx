// components/Layout/Header.jsx
import { useEffect, useState } from 'react';
import { getHealth } from '../../services/api';

export default function Header({ onClearChat }) {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const check = async () => {
      try { setHealth(await getHealth()); }
      catch { setHealth(null); }
    };
    check();
    const t = setInterval(check, 30000);
    return () => clearInterval(t);
  }, []);

  const isOnline = health?.status === 'ok';

  return (
    <header className="header">
      <div className="header-logo">
        <div className="header-logo-icon">⚖️</div>
        <div>
          <div className="header-title">RAG Legal Bot</div>
          <div className="header-subtitle">مستشارك القانوني الذكي</div>
        </div>
      </div>
      <div className="header-spacer" />
      <div className="health-badge">
        <div className={`health-dot ${!isOnline ? 'offline' : ''}`} />
        <span style={{ fontSize: 12, color: isOnline ? '#3ecf8e' : '#f56565' }}>
          {health ? (isOnline ? 'Online' : 'Degraded') : 'Connecting...'}
        </span>
      </div>
      {onClearChat && (
        <button className="btn btn-ghost" onClick={onClearChat} style={{ marginLeft: 8 }}>
          🗑 Effacer
        </button>
      )}
    </header>
  );
}
