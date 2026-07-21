"""
database.py
------------
All SQLite access for QR Code Cracker lives here. This is intentionally kept
separate from app.py so the storage layer can be swapped later (e.g. to
Postgres) without touching route logic.
"""

import os
import sqlite3
from datetime import datetime

# Always place the database next to this file, regardless of working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BASE_DB_PATH = os.path.join(_HERE, "qr_cracker.db")

# Vercel Serverless environment support (writeable /tmp)
if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
    DB_PATH = "/tmp/qr_cracker.db"
    if not os.path.exists(DB_PATH) and os.path.exists(_BASE_DB_PATH):
        import shutil
        try:
            shutil.copy2(_BASE_DB_PATH, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = _BASE_DB_PATH


def get_connection():
    """Return a connection with row access by column name."""
    # Ensure tables are initialized if DB path is newly created in /tmp
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't already exist. Safe to call on every startup."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dynamic_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_id TEXT UNIQUE NOT NULL,
            qr_type TEXT NOT NULL,
            target_content TEXT NOT NULL,
            filename TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_id TEXT NOT NULL,
            scanned_at TEXT NOT NULL,
            device_type TEXT,
            FOREIGN KEY (short_id) REFERENCES dynamic_codes (short_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS custom_ciphers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mapping_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ---------- dynamic_codes ----------

def create_dynamic_code(short_id: str, qr_type: str, target_content: str, filename: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO dynamic_codes (short_id, qr_type, target_content, filename, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (short_id, qr_type, target_content, filename, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_dynamic_code(short_id: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM dynamic_codes WHERE short_id = ?", (short_id,)
    ).fetchone()
    conn.close()
    return row


def update_target(short_id: str, new_target: str):
    """Change where a dynamic code points, without touching the QR image itself."""
    conn = get_connection()
    conn.execute(
        "UPDATE dynamic_codes SET target_content = ? WHERE short_id = ?",
        (new_target, short_id),
    )
    conn.commit()
    conn.close()


def get_all_codes():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM dynamic_codes ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return rows


def delete_code(short_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM dynamic_codes WHERE short_id = ?", (short_id,))
    conn.execute("DELETE FROM scans WHERE short_id = ?", (short_id,))
    conn.commit()
    conn.close()


# ---------- scans ----------

def log_scan(short_id: str, device_type: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO scans (short_id, scanned_at, device_type) VALUES (?, ?, ?)",
        (short_id, datetime.utcnow().isoformat(), device_type),
    )
    conn.commit()
    conn.close()


def get_scan_count(short_id: str) -> int:
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) as c FROM scans WHERE short_id = ?", (short_id,)
    ).fetchone()["c"]
    conn.close()
    return count


def get_scans_for_code(short_id: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM scans WHERE short_id = ? ORDER BY scanned_at DESC", (short_id,)
    ).fetchall()
    conn.close()
    return rows

# ---------- custom_ciphers ----------

def create_custom_cipher(name: str, mapping_json: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO custom_ciphers (name, mapping_json, created_at) VALUES (?, ?, ?)",
        (name, mapping_json, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def get_custom_ciphers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM custom_ciphers ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows

def get_custom_cipher(cipher_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM custom_ciphers WHERE id = ?", (cipher_id,)).fetchone()
    conn.close()
    return row

def delete_custom_cipher(cipher_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM custom_ciphers WHERE id = ?", (cipher_id,))
    conn.commit()
    conn.close()
