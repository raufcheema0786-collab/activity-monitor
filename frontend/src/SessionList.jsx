import { useEffect, useState } from "react";

function SessionList({ onSelect, onBack }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    window.pywebview.api.get_sessions().then((data) => {
      setSessions(data);
      setLoading(false);
    });
  }, []);

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="app-shell">
      <div className="topbar">
        <button className="btn btn-ghost" onClick={onBack}>← Back</button>
        <h1>Past sessions</h1>
      </div>

      {loading ? (
        <p className="empty-state">Loading…</p>
      ) : sessions.length === 0 ? (
        <p className="empty-state">No sessions yet.</p>
      ) : (
        <ul className="list">
          {sessions.map((s) => {
            const running = !s.end_time;
            return (
              <li key={s.id}>
                <button className="list-item" onClick={() => onSelect(s.id)}>
                  <span>
                    <span className="list-item-title">Session #{s.id}</span>
                    <br />
                    <span className="list-item-sub">{s.start_time}</span>
                  </span>
                  <span className={`pill ${running ? "pill-active" : "pill-not_tracking"}`}>
                    <span className="pill-dot" />
                    {running ? "Running" : formatDuration(s.duration ?? 0)}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default SessionList;
