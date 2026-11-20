"""db.py - everything about the database (SQLite) lives here."""
import sqlite3

DB_FILE = "tasks.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # lets us read rows like dictionaries
    return conn


def init_db():
    """Create the tables if they do not exist yet."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            raw_notes TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            owner TEXT,
            due TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            FOREIGN KEY (meeting_id) REFERENCES meetings (id)
        )
        """
    )
    conn.commit()
    conn.close()


def add_meeting(title, raw_notes):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO meetings (title, raw_notes) VALUES (?, ?)", (title, raw_notes)
    )
    conn.commit()
    meeting_id = cur.lastrowid
    conn.close()
    return meeting_id


def add_task(meeting_id, task, owner=None, due=None, priority="medium"):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO tasks (meeting_id, task, owner, due, priority) VALUES (?, ?, ?, ?, ?)",
        (meeting_id, task, owner, due, priority),
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id


def get_tasks(owner=None, status=None):
    """Return tasks, optionally filtered by owner and/or status."""
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if owner:
        query += " AND owner = ?"
        params.append(owner)
    if status:
        query += " AND status = ?"
        params.append(status)
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    # Quick self-test: run `python db.py`
    init_db()
    mid = add_meeting("Test meeting", "Ravi will send the report by Friday.")
    add_task(mid, "Send the report", owner="Ravi", due="Friday")
    print(get_tasks())
