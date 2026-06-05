
import sqlite3  # no installation needed

DB_NAME = "tasks.db"   # The file where tasks will be saved

def init_db():
    """Create the tasks table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_text TEXT NOT NULL,
            remind_at TEXT,          -- stores date & time as text
            is_done INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_task(user_id: int, task_text: str, remind_at: str = None):
    """Insert a new task and return its ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, task_text, remind_at) VALUES (?, ?, ?)",
              (user_id, task_text, remind_at))
    conn.commit()
    task_id = c.lastrowid
    conn.close()
    return task_id

def get_tasks(user_id: int, only_pending=True):
    """Retrieve tasks for a user. If only_pending=True, show only unfinished ones."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if only_pending:
        c.execute("SELECT id, task_text, remind_at, is_done FROM tasks WHERE user_id=? AND is_done=0", (user_id,))
    else:
        c.execute("SELECT id, task_text, remind_at, is_done FROM tasks WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_done(task_id: int, user_id: int):
    """Mark a task as done. Returns True if successful."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE tasks SET is_done=1 WHERE id=? AND user_id=?", (task_id, user_id))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0

def delete_task(task_id: int, user_id: int):
    """Delete a task. Returns True if it existed and was deleted."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, user_id))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0

def delete_all_tasks(user_id: int):
    """Delete all tasks for a user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()