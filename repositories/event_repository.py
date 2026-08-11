import json
from datetime import datetime
from storage.database import get_connection

def save_event(session_id, event_type, metadata=None, client_ref=None, employee_id=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO events (session_id, event_type, timestamp, metadata, client_ref, employee_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, event_type, datetime.now().isoformat(), json.dumps(metadata or {}), client_ref, employee_id),
    )
    conn.commit()
    conn.close()

def get_events_for_session(session_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM events WHERE session_id = ? ORDER BY timestamp", (session_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_events_by_type(session_id, event_type):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM events WHERE session_id = ? AND event_type = ? ORDER BY timestamp",
        (session_id, event_type)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
