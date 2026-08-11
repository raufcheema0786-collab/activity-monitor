import json
from datetime import datetime
from storage.database import get_connection

MAX_RETRY_ATTEMPTS = 10


def queue_upload(upload_type, payload, client_ref=None, employee_id=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO pending_uploads (upload_type, payload, client_ref, employee_id, created_at, retry_count, status) "
        "VALUES (?, ?, ?, ?, ?, 0, 'pending')",
        (upload_type, json.dumps(payload), client_ref, employee_id, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_pending_uploads(employee_id=None):
    # Scoped to the currently active employee by default: a queued upload
    # left behind by a previous employee on this machine must never be
    # sent under a different employee's auth token -- it would silently
    # attribute their work to the wrong person on the backend. It stays
    # queued (never sent, never deleted) unless that original employee's
    # credentials become active on this machine again.
    conn = get_connection()
    if employee_id is not None:
        rows = conn.execute(
            "SELECT * FROM pending_uploads WHERE status = 'pending' AND employee_id = ? ORDER BY id ASC",
            (employee_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM pending_uploads WHERE status = 'pending' ORDER BY id ASC"
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_upload_succeeded(upload_id):
    conn = get_connection()
    conn.execute("DELETE FROM pending_uploads WHERE id = ?", (upload_id,))
    conn.commit()
    conn.close()


def mark_upload_failed(upload_id, error, abandon=False):
    conn = get_connection()
    conn.execute(
        "UPDATE pending_uploads SET retry_count = retry_count + 1, last_attempt_at = ?, "
        "last_error = ?, status = ? WHERE id = ?",
        (
            datetime.now().isoformat(),
            str(error)[:500] if error else None,
            "abandoned" if abandon else "pending",
            upload_id,
        ),
    )
    conn.commit()
    conn.close()
