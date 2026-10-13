import os
import sqlite3
from config import DATABASE
from werkzeug.security import generate_password_hash


def get_db_connection():
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE)), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            worker_id TEXT,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # DETECTIONS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            mode TEXT,
            result TEXT,
            response_level TEXT,
            confidence REAL,
            dominant_color TEXT,
            image_path TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # SESSIONS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            logout_time TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Check whether users already exist
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:

        # Manager account
        cursor.execute("""
            INSERT INTO users
            (name, username, password, role, worker_id, department)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Project Manager",
            "manager",
            generate_password_hash("manager123"),
            "manager",
            None,
            "Management"
        ))

        # Worker 1
        cursor.execute("""
            INSERT INTO users
            (name, username, password, role, worker_id, department)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Worker One",
            "worker1",
            generate_password_hash("worker123"),
            "worker",
            "W001",
            "Production"
        ))

        # Worker 2
        cursor.execute("""
            INSERT INTO users
            (name, username, password, role, worker_id, department)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Worker Two",
            "worker2",
            generate_password_hash("worker123"),
            "worker",
            "W002",
            "Maintenance"
        ))

    # Keep the standard worker accounts available after upgrades too.
    # Existing custom workers are preserved.
    default_workers = [
        ("Worker Three", "worker3", "W003", "Operations")
    ]

    for name, username, worker_id, department in default_workers:
        cursor.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username,)
        )

        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO users
                (name, username, password, role, worker_id, department)
                VALUES (?, ?, ?, 'worker', ?, ?)
            """, (
                name,
                username,
                generate_password_hash("worker123"),
                worker_id,
                department
            ))

    conn.commit()
    conn.close()
def get_user_by_username(username):
    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    conn.close()

    return user