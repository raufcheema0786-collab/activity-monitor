import sqlite3

DB_PATH = "monitor.db"

# Columns added after the initial schema was created. schema.sql's
# CREATE TABLE IF NOT EXISTS won't retrofit these onto an existing
# monitor.db, so we add them by hand for anyone upgrading in place.
_MIGRATIONS = [
    ("sessions", "client_ref", "TEXT"),
    ("events", "client_ref", "TEXT"),
    ("screenshots", "client_ref", "TEXT"),
    ("pending_uploads", "client_ref", "TEXT"),
    ("pending_uploads", "last_attempt_at", "TEXT"),
    ("pending_uploads", "retry_count", "INTEGER NOT NULL DEFAULT 0"),
    ("pending_uploads", "last_error", "TEXT"),
    ("pending_uploads", "status", "TEXT NOT NULL DEFAULT 'pending'"),
    ("sessions", "employee_id", "INTEGER"),
    ("events", "employee_id", "INTEGER"),
    ("screenshots", "employee_id", "INTEGER"),
    ("pending_uploads", "employee_id", "INTEGER"),
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _existing_columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _run_migrations(conn):
    for table, column, ddl_type in _MIGRATIONS:
        if column not in _existing_columns(conn, table):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")


def init_db():
    conn = get_connection()
    with open("schema.sql") as f:
        conn.executescript(f.read())
    _run_migrations(conn)
    # Created here rather than in schema.sql: on an existing database the
    # status column above may not exist until the migration above adds it.
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pending_uploads_status_id ON pending_uploads(status, id)")
    conn.commit()
    conn.close()
