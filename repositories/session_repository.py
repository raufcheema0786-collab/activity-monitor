from storage.database import get_connection

def create_session(start_time):
    conn = get_connection()
    cursor = conn.execute("INSERT INTO sessions (start_time) VALUES (?)", (start_time,))
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id

def end_session(session_id, end_time, stats):
    conn = get_connection()
    conn.execute(
        "UPDATE sessions SET end_time = ?, duration = ?, active_time = ?, idle_time = ? WHERE id = ?",
        (end_time, stats["duration"], stats["active_time"], stats["idle_time"], session_id)
    )
    conn.commit()
    conn.close()

def get_session_by_id(session_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_sessions():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM sessions ORDER BY start_time DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_latest_session():
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM sessions ORDER BY start_time DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None
