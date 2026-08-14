import { useState, useEffect, useRef } from "react";
import Login from "./Login";
import SessionList from "./SessionList";
import SessionDetails from "./SessionDetails";
import StatusView from "./StatusView";

function App() {
  const [user, setUser] = useState(null);
  const [screen, setScreen] = useState("main");
  const [working, setWorking] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [seconds, setSeconds] = useState(0);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (working) {
      intervalRef.current = setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [working]);

  const formatTime = (total) => {
    const h = String(Math.floor(total / 3600)).padStart(2, "0");
    const m = String(Math.floor((total % 3600) / 60)).padStart(2, "0");
    const s = String(total % 60).padStart(2, "0");
    return `${h}:${m}:${s}`;
  };

  const startWork = async () => {
    const id = await window.pywebview.api.start_work();
    setSessionId(id);
    setSeconds(0);
    setWorking(true);
  };

  const stopWork = async () => {
    await window.pywebview.api.stop_work();
    setWorking(false);
  };

  if (!user) {
    return <Login onLogin={(name) => setUser(name)} />;
  }

  if (screen === "sessions") {
    return (
      <SessionList
        onBack={() => setScreen("main")}
        onSelect={(id) => {
          setSelectedSessionId(id);
          setScreen("details");
        }}
      />
    );
  }

  if (screen === "details") {
    return (
      <SessionDetails
        sessionId={selectedSessionId}
        onBack={() => setScreen("sessions")}
      />
    );
  }

  if (screen === "status") {
    return <StatusView onBack={() => setScreen("main")} />;
  }

  return (
    <div className="app-shell">
      <div className="topbar">
        <h1>Activity Monitor</h1>
      </div>

      <div className="card" style={{ textAlign: "center", padding: "36px 24px" }}>
        <p style={{ color: "var(--text-muted)", fontSize: 13.5, marginBottom: 18 }}>
          Signed in as <strong style={{ color: "var(--text)" }}>{user}</strong>
        </p>

        {working ? (
          <>
            <div className="mono" style={{ fontSize: 40, fontWeight: 650, letterSpacing: "-0.02em", marginBottom: 20 }}>
              {formatTime(seconds)}
            </div>
            <button className="btn" style={{ borderColor: "var(--danger)", color: "var(--danger)" }} onClick={stopWork}>
              Stop work
            </button>
          </>
        ) : (
          <button className="btn btn-primary" onClick={startWork}>
            Start work
          </button>
        )}

        {sessionId && (
          <p style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 14 }}>
            Session #{sessionId}
          </p>
        )}
      </div>

      <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
        <button className="btn" onClick={() => setScreen("sessions")}>
          Past sessions
        </button>
        <button className="btn" onClick={() => setScreen("status")}>
          My status
        </button>
      </div>
    </div>
  );
}

export default App;
