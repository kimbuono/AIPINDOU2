"""
Database layer — SQLite with aiosqlite.

Tables:
  - users: account info
  - projects: saved bead-art projects

Schema is auto-created on first access.
"""

import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "aipindou.db"))


def _ensure_dir():
    d = os.path.dirname(DB_PATH)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    NOT NULL UNIQUE,
            username    TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL DEFAULT '未命名项目',
            -- core params
            grid_size   INTEGER NOT NULL DEFAULT 48,
            n_colors    INTEGER NOT NULL DEFAULT 48,
            brand       TEXT    NOT NULL DEFAULT 'artkal',
            dither      INTEGER NOT NULL DEFAULT 1,
            -- image data (base64 encoded)
            original_image  TEXT,
            blueprint_image TEXT,
            -- stats snapshot
            stats_json  TEXT,
            -- metadata
            is_favorite INTEGER NOT NULL DEFAULT 0,
            is_public   INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
        CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects(updated_at DESC);
    """)
    conn.commit()
    conn.close()


# Run on import
init_db()
