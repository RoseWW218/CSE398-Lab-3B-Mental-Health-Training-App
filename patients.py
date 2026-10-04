import sqlite3

from auth import connect_db


# Fictional profiles adapted from the assignment examples.
PRESET_PATIENTS = {
    "Anxiety / Panic — Alex": {
        "name": "Alex",
        "gender": "Non-binary",
        "age_group": "18–25",
        "ethnicity": "Not specified",
        "concern": "Academic stress and anxiety",
        "background": (
            "A 24-year-old university student who feels overwhelmed "
            "by upcoming final exams and worries about disappointing "
            "their family."
        ),
        "communication_style": (
            "Speaks quickly, hesitates to open up, and gradually "
            "shares more when they feel understood."
        ),
        "key_symptoms": (
            "Frequent worry, difficulty sleeping, trouble concentrating, "
            "and occasional feelings of panic."
        ),
    },
    "Depression — Jordan": {
        "name": "Jordan",
        "gender": "Male",
        "age_group": "36–45",
        "ethnicity": "Not specified",
        "concern": "Low mood and lack of motivation",
        "background": (
            "A 40-year-old remote worker who has become socially "
            "isolated and finds it difficult to stay engaged "
            "with work and daily routines."
        ),
        "communication_style": (
            "Quiet, gives brief responses, and needs gentle "
            "open-ended questions to elaborate."
        ),
        "key_symptoms": (
            "Low mood, reduced interest in usual activities, "
            "low energy, and lack of motivation."
        ),
    },
    "Burnout — Morgan": {
        "name": "Morgan",
        "gender": "Female",
        "age_group": "26–35",
        "ethnicity": "Not specified",
        "concern": "Work-related burnout",
        "background": (
            "A 32-year-old high-achieving professional who regularly "
            "works long hours and feels pressure to maintain "
            "excellent performance."
        ),
        "communication_style": (
            "Reluctant to show weakness, rationalizes emotions, "
            "and initially minimizes personal difficulties."
        ),
        "key_symptoms": (
            "Emotional exhaustion, irritability, difficulty relaxing, "
            "and reduced satisfaction with work."
        ),
    },
}


def initialize_patients():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                name TEXT NOT NULL,
                gender TEXT NOT NULL,
                age_group TEXT NOT NULL,
                ethnicity TEXT NOT NULL,
                concern TEXT NOT NULL,
                background TEXT NOT NULL,
                communication_style TEXT NOT NULL DEFAULT '',
                key_symptoms TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)

        # Update a database created by the earlier version.
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(patients)")
        }

        for column in ("communication_style", "key_symptoms"):
            if column not in columns:
                conn.execute(
                    f"ALTER TABLE patients ADD COLUMN {column} "
                    "TEXT NOT NULL DEFAULT ''"
                )


def create_patient(
    username,
    name,
    gender,
    age_group,
    ethnicity,
    concern,
    background,
    communication_style="",
    key_symptoms="",
):
    initialize_patients()

    with connect_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO patients (
                username, name, gender, age_group,
                ethnicity, concern, background,
                communication_style, key_symptoms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                name,
                gender,
                age_group,
                ethnicity,
                concern,
                background,
                communication_style,
                key_symptoms,
            ),
        )
        return cursor.lastrowid


def list_patients(username):
    initialize_patients()

    with connect_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT * FROM patients
            WHERE username = ?
            ORDER BY created_at DESC, id DESC
            """,
            (username,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_patient(username, patient_id):
    initialize_patients()

    with connect_db() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT * FROM patients
            WHERE username = ? AND id = ?
            """,
            (username, patient_id),
        ).fetchone()

    return dict(row) if row else None