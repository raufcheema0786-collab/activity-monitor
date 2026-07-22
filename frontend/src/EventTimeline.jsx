function EventTimeline({ events }) {
  return (
    <div style={{ textAlign: "left", maxWidth: "500px", margin: "20px auto" }}>
      <h3>Event Timeline</h3>
      {events.length === 0 && <p>No events recorded.</p>}
      <ul>
        {events.map((event) => (
          <li key={event.id}>
            {new Date(event.timestamp).toLocaleTimeString()} — {event.event_type}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default EventTimeline;
