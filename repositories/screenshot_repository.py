from datetime import datetime
from storage.database import get_connection

def save_screenshot(session_id, path, client_ref=None, employee_id=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO screenshots (session_id, path, captured_at, client_ref, employee_id) VALUES (?, ?, ?, ?, ?)",
        (session_id, path, datetime.now().isoformat(), client_ref, employee_id),
    )
    conn.commit()
    conn.close()

def get_screenshots_for_session(session_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM screenshots WHERE session_id = ? ORDER BY captured_at", (session_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
