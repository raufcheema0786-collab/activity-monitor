import { useEffect, useState } from "react";

function SessionList({ onSelect, onBack }) {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    window.pywebview.api.get_sessions().then(setSessions);
  }, []);

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div style={{ padding: "40px", textAlign: "center" }}>
      <button onClick={onBack}>Back</button>
      <h2>Past Sessions</h2>
      {sessions.length === 0 && <p>No sessions yet.</p>}
      <ul style={{ listStyle: "none", padding: 0 }}>
        {sessions.map((s) => {
          const status = s.end_time ? "Ended" : "Running";
          const duration = s.end_time ? formatDuration(s.duration ?? 0) : "Running";
          return (
            <li key={s.id} style={{ marginBottom: "10px" }}>
              <button onClick={() => onSelect(s.id)}>
                Session {s.id} — {s.start_time} — {status} — {duration}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default SessionList;
