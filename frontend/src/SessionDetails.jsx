import { useEffect, useState } from "react";
import EventTimeline from "./EventTimeline";
import ScreenshotGallery from "./ScreenshotGallery";

function SessionDetails({ sessionId, onBack }) {
  const [details, setDetails] = useState(null);

  useEffect(() => {
    window.pywebview.api.get_session_details(sessionId).then(setDetails);
  }, [sessionId]);

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  if (!details) {
    return (
      <div className="app-shell">
        <div className="topbar">
          <button className="btn btn-ghost" onClick={onBack}>← Back</button>
          <h1>Session</h1>
        </div>
        <p className="empty-state">Loading…</p>
      </div>
    );
  }

  const { session, events, screenshots } = details;
  const duration = session.duration != null ? formatDuration(session.duration) : "Running";
  const activeTime = session.active_time != null ? formatDuration(session.active_time) : "0m 0s";
  const idleTime = session.idle_time != null ? formatDuration(session.idle_time) : "0m 0s";

  return (
    <div className="app-shell">
      <div className="topbar">
        <button className="btn btn-ghost" onClick={onBack}>← Back to sessions</button>
        <h1>Session #{session.id}</h1>
      </div>

      <div className="card">
        <table className="data-table">
          <tbody>
            <tr>
              <td>Start</td>
              <td className="mono">{session.start_time}</td>
            </tr>
            <tr>
              <td>End</td>
              <td className="mono">{session.end_time || "Still running"}</td>
            </tr>
            <tr>
              <td>Duration</td>
              <td className="mono">{duration}</td>
            </tr>
            <tr>
              <td>Active time</td>
              <td className="mono">{activeTime}</td>
            </tr>
            <tr>
              <td>Idle time</td>
              <td className="mono">{idleTime}</td>
            </tr>
            <tr>
              <td>Events recorded</td>
              <td className="mono">{events.length}</td>
            </tr>
            <tr>
              <td>Screenshots captured</td>
              <td className="mono">{screenshots.length}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 style={{ marginBottom: 12 }}>Event timeline</h2>
        <EventTimeline events={events} />
      </div>

      <div className="card">
        <h2 style={{ marginBottom: 12 }}>Screenshots</h2>
        <ScreenshotGallery screenshots={screenshots} />
      </div>
    </div>
  );
}

export default SessionDetails;
