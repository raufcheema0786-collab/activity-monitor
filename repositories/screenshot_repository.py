from datetime import datetime
from storage.database import get_connection

def save_screenshot(session_id, path):
    conn = get_connection()
    conn.execute(
        "INSERT INTO screenshots (session_id, path, captured_at) VALUES (?, ?, ?)",
        (session_id, path, datetime.now().isoformat())
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
