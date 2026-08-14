function EventTimeline({ events }) {
  if (events.length === 0) return <p className="empty-state">No events recorded.</p>;

  return (
    <ul className="timeline">
      {events.map((event) => (
        <li key={event.id}>
          <span className="timeline-time">{new Date(event.timestamp).toLocaleTimeString()}</span>
          {event.event_type}
        </li>
      ))}
    </ul>
  );
}

export default EventTimeline;
