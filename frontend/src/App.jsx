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
    <div style={{ padding: "40px", textAlign: "center" }}>
      <h1>Activity Monitor</h1>
      <p>Welcome, {user}</p>

      {working ? (
        <>
          <h2>{formatTime(seconds)}</h2>
          <button onClick={stopWork}>Stop Work</button>
        </>
      ) : (
        <button onClick={startWork}>Start Work</button>
      )}

      {sessionId && <p>Current session id: {sessionId}</p>}

      <div style={{ marginTop: "30px" }}>
        <button onClick={() => setScreen("sessions")}>View Past Sessions</button>
        <button style={{ marginLeft: "10px" }} onClick={() => setScreen("status")}>
          My Status
        </button>
      </div>
    </div>
  );
}

export default App;
