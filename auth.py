import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path

import streamlit as st

DB_PATH = Path(__file__).resolve().parent / "counseling.db"


def connect_db():
    return sqlite3.connect(DB_PATH, timeout=10)


def initialize_users():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        600_000,
    ).hex()


def require_login():
    initialize_users()

    if st.session_state.get("username"):
        with st.sidebar:
            st.write(f"Signed in as: {st.session_state.username}")
            if st.button("Log out"):
                st.session_state.clear()
                st.rerun()
        return st.session_state.username

    login_tab, register_tab = st.tabs(["Log in", "Register"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")

        if submitted:
            with connect_db() as conn:
                row = conn.execute(
                    "SELECT salt, password_hash FROM users WHERE username = ?",
                    (username.strip(),),
                ).fetchone()

            if row and hmac.compare_digest(
                hash_password(password, row[0]), row[1]
            ):
                st.session_state.username = username.strip()
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input(
                "Choose a password", type="password"
            )
            confirm_password = st.text_input(
                "Confirm password", type="password"
            )
            register = st.form_submit_button("Create account")

        if register:
            new_username = new_username.strip()

            if not new_username:
                st.error("Please enter a username.")
            elif len(new_password) < 8:
                st.error("Password must contain at least 8 characters.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                salt = secrets.token_hex(16)
                password_hash = hash_password(new_password, salt)

                try:
                    with connect_db() as conn:
                        conn.execute(
                            "INSERT INTO users VALUES (?, ?, ?)",
                            (new_username, salt, password_hash),
                        )
                    st.success("Account created. Please use the Log in tab.")
                except sqlite3.IntegrityError:
                    st.error("This username already exists.")

    st.stop()