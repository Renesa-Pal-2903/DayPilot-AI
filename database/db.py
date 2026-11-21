
import sqlite3
from pathlib import Path


# ==================================================
# DATABASE CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "daypilot.db"


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================================================
# INITIALIZE DATABASE
# ==================================================

def initialize_database():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            deadline TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            estimated_minutes INTEGER DEFAULT 60,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    existing_columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(tasks)"
        ).fetchall()
    }

    migrations = {
        "description": "TEXT",
        "deadline": "TEXT",
        "priority": "TEXT DEFAULT 'Medium'",
        "status": "TEXT DEFAULT 'Pending'",
        "estimated_minutes": "INTEGER DEFAULT 60",
        "created_at": "TEXT"
    }

    for column, definition in migrations.items():

        if column not in existing_columns:
            conn.execute(
                f"ALTER TABLE tasks ADD COLUMN {column} {definition}"
            )

    conn.commit()
    conn.close()


# ==================================================
# ADD TASK
# ==================================================

def add_task(
    title,
    description="",
    deadline=None,
    priority="Medium",
    estimated_minutes=60
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO tasks (
            title,
            description,
            deadline,
            priority,
            status,
            estimated_minutes
        )
        VALUES (?, ?, ?, ?, 'Pending', ?)
    """, (
        title,
        description,
        deadline,
        priority,
        estimated_minutes
    ))

    conn.commit()
    conn.close()


# ==================================================
# GET ALL TASKS
# ==================================================

def get_tasks():

    conn = get_connection()

    tasks = conn.execute("""
        SELECT *
        FROM tasks
        ORDER BY
            CASE
                WHEN deadline IS NULL OR deadline = ''
                THEN 1 ELSE 0
            END,
            deadline ASC,
            id DESC
    """).fetchall()

    conn.close()

    return [dict(task) for task in tasks]


# ==================================================
# GET TASK BY ID
# ==================================================

def get_task_by_id(task_id):

    conn = get_connection()

    task = conn.execute("""
        SELECT *
        FROM tasks
        WHERE id = ?
    """, (task_id,)).fetchone()

    conn.close()

    return dict(task) if task else None


# ==================================================
# COMPLETE TASK
# ==================================================

def complete_task(task_id):

    conn = get_connection()

    conn.execute("""
        UPDATE tasks
        SET status = 'Completed'
        WHERE id = ?
    """, (task_id,))

    conn.commit()
    conn.close()


# ==================================================
# DELETE TASK
# ==================================================

def delete_task(task_id):

    conn = get_connection()

    conn.execute("""
        DELETE FROM tasks
        WHERE id = ?
    """, (task_id,))

    conn.commit()
    conn.close()
