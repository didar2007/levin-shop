
import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "bot/levin.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_user(user_id, first_name="", username=""):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users (telegram_id, first_name, username)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                first_name = excluded.first_name,
                username = excluded.username
        """, (user_id, first_name, username))


def get_all_users():
    with get_connection() as conn:
        return conn.execute(
            "SELECT telegram_id FROM users"
        ).fetchall()


def get_users_count():
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]
