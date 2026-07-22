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

  if (!details) return <p>Loading...</p>;

  const { session, events, screenshots } = details;
  const duration = session.duration != null ? formatDuration(session.duration) : "Running";
  const activeTime = session.active_time != null ? formatDuration(session.active_time) : "0m 0s";
  const idleTime = session.idle_time != null ? formatDuration(session.idle_time) : "0m 0s";
  const eventCount = events.length;
  const screenshotCount = screenshots.length;

  return (
    <div style={{ padding: "40px", textAlign: "center" }}>
      <button onClick={onBack}>Back to Sessions</button>
      <h2>Session {session.id}</h2>
      <p>Start: {session.start_time}</p>
      <p>End: {session.end_time || "Still running"}</p>
      <p>Duration: {duration}</p>
      <p>Active time: {activeTime}</p>
      <p>Idle time: {idleTime}</p>
      <p>Events recorded: {eventCount}</p>
      <p>Screenshots captured: {screenshotCount}</p>

      <EventTimeline events={events} />
      <ScreenshotGallery screenshots={screenshots} />
    </div>
  );
}

export default SessionDetails;
