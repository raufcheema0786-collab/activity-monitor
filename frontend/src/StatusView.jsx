import { useEffect, useState } from "react";

const POLL_INTERVAL_MS = 5000;

const STATUS_LABELS = {
  active: "Active",
  idle: "Idle",
  not_tracking: "Not tracking",
};

function formatDuration(totalSeconds) {
  const total = Math.max(0, Math.floor(totalSeconds || 0));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function formatRelativeTime(isoString) {
  if (!isoString) return "Never (not clocked in yet, or no heartbeat has succeeded)";
  const then = new Date(isoString).getTime();
  if (Number.isNaN(then)) return "Unknown";
  const seconds = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (seconds < 5) return "Just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m ago`;
}

function StatusView({ onBack }) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const fetchStatus = () => {
      window.pywebview.api
        .get_status()
        .then((data) => {
          if (!cancelled) {
            setStatus(data);
            setError("");
          }
        })
        .catch((err) => {
          if (!cancelled) setError("Unable to load status: " + String(err));
        });
    };

    fetchStatus();
    const intervalId = setInterval(fetchStatus, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, []);

  const settings = status?.settings;

  return (
    <div className="app-shell">
      <div className="topbar">
        <button className="btn btn-ghost" onClick={onBack}>← Back</button>
        <h1>My status</h1>
      </div>

      {error && <div className="notice notice-danger">{error}</div>}

      {!status ? (
        <p className="empty-state">Loading…</p>
      ) : (
        <>
          {status.sync_auth_failed && (
            <div className="notice notice-warn">
              <strong>Heads up:</strong> this app hasn't been able to reach the monitoring server (your login may
              have expired). The numbers below reflect what's tracked on this computer, but they haven't been
              confirmed by the server yet, and your admin's dashboard may not match. Contact your admin if this
              doesn't clear up on its own.
            </div>
          )}

          <div className="card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <span className={`pill pill-${status.tracking_status}`}>
              <span className="pill-dot" />
              {STATUS_LABELS[status.tracking_status] ?? "Not tracking"}
            </span>

            <table className="data-table">
              <tbody>
                <tr>
                  <td>Current session duration</td>
                  <td className="mono">
                    {status.tracking_status === "not_tracking" ? "Not clocked in" : formatDuration(status.session_duration_seconds)}
                  </td>
                </tr>
                <tr>
                  <td>Active time today</td>
                  <td className="mono">{formatDuration(status.today_active_seconds)}</td>
                </tr>
                <tr>
                  <td>Idle time today</td>
                  <td className="mono">{formatDuration(status.today_idle_seconds)}</td>
                </tr>
                <tr>
                  <td>Last heartbeat sent to server</td>
                  <td className="mono">{formatRelativeTime(status.last_heartbeat_at)}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="card" style={{ fontSize: 13, lineHeight: 1.6 }}>
            <h2 style={{ marginBottom: 10 }}>What this app tracks while you're clocked in</h2>
            <ul style={{ margin: 0, paddingLeft: 20, display: "flex", flexDirection: "column", gap: 8 }}>
              <li>
                <strong>Keyboard &amp; mouse activity</strong> — the app notices that you pressed a key or moved/clicked
                the mouse, only to tell whether you're active or idle. It does not log which keys, what you typed,
                mouse coordinates, or a record of individual keystrokes/clicks.
              </li>
              <li>
                <strong>Idle detection</strong> — if there's no keyboard/mouse activity for{" "}
                {settings ? `${settings.idle_timeout_seconds} seconds` : "a configured period"}, you're marked idle until
                the next input.
              </li>
              <li>
                <strong>Periodic screenshots</strong> — a screenshot of your screen roughly every{" "}
                {settings ? `${settings.screenshot_interval_seconds} seconds` : "configured interval"} while you're
                clocked in.
              </li>
              <li>
                <strong>Session timing</strong> — when you start/stop work, and a heartbeat every{" "}
                {settings ? `${settings.heartbeat_interval_seconds} seconds` : "configured interval"} so the server knows
                the app is running.
              </li>
            </ul>
            <p style={{ marginTop: 12 }}>
              This app does not read keystroke content, browser history, clipboard contents, files, camera, or
              microphone. Nothing is tracked while you're not clocked in.
            </p>
            <p style={{ marginTop: 8, color: "var(--text-muted)" }}>
              This screen is read-only — it shows your status but can't be used to pause or change tracking.
            </p>
          </div>
        </>
      )}
    </div>
  );
}

export default StatusView;
