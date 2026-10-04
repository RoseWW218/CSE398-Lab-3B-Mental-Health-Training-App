import json
import sqlite3

from auth import DB_PATH


def connect_db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_sessions():
    with connect_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                patient_id INTEGER NOT NULL,
                messages_json TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                feedback TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_session(username, patient_id, messages, summary="", feedback=""):
    initialize_sessions()

    with connect_db() as connection:
        patient = connection.execute(
            "SELECT id FROM patients WHERE id = ? AND username = ?",
            (patient_id, username),
        ).fetchone()

        if patient is None:
            raise ValueError("Patient not found for this account.")

        cursor = connection.execute("""
            INSERT INTO sessions
                (username, patient_id, messages_json, summary, feedback)
            VALUES (?, ?, ?, ?, ?)
        """, (
            username,
            patient_id,
            json.dumps(messages, ensure_ascii=False),
            summary,
            feedback,
        ))

        return cursor.lastrowid


def update_session_feedback(username, session_id, feedback):
    initialize_sessions()

    with connect_db() as connection:
        connection.execute("""
            UPDATE sessions
            SET feedback = ?
            WHERE id = ? AND username = ?
        """, (feedback, session_id, username))


def list_sessions(username, patient_id):
    initialize_sessions()

    with connect_db() as connection:
        rows = connection.execute("""
            SELECT id, patient_id, summary, feedback, created_at
            FROM sessions
            WHERE username = ? AND patient_id = ?
            ORDER BY id DESC
        """, (username, patient_id)).fetchall()

        return [dict(row) for row in rows]


def get_session(username, session_id):
    initialize_sessions()

    with connect_db() as connection:
        row = connection.execute("""
            SELECT *
            FROM sessions
            WHERE id = ? AND username = ?
        """, (session_id, username)).fetchone()

    if row is None:
        return None

    session = dict(row)
    session["messages"] = json.loads(session.pop("messages_json"))
    return session

def update_session_summary(username, session_id, summary):
    initialize_sessions()

    with connect_db() as connection:
        connection.execute(
            """
            UPDATE sessions
            SET summary = ?
            WHERE id = ? AND username = ?
            """,
            (summary, session_id, username),
        )