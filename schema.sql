CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT,
    end_time TEXT,
    duration INTEGER,
    active_time INTEGER,
    idle_time INTEGER,
    client_ref TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    event_type TEXT,
    timestamp TEXT,
    metadata TEXT,
    client_ref TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS screenshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    path TEXT,
    captured_at TEXT,
    client_ref TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Queue of outgoing syncs (heartbeat, session start/end, event, screenshot)
-- that failed to reach the backend and are waiting to be retried.
CREATE TABLE IF NOT EXISTS pending_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    client_ref TEXT,
    created_at TEXT NOT NULL,
    last_attempt_at TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
);
