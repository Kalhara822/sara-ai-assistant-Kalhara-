"""
SQLite Memory Engine for SARA AI Assistant
Stores: conversation history, notes/reminders, preferences, app usage stats.
Implements semantic memory interface ready for future vector DB integration.
"""

import sqlite3
import json
import time
import threading
from typing import Optional, List, Dict, Any
from pathlib import Path
from config import config
from utils.logger import logger


class MemoryManager:
    """
    Thread-safe SQLite memory manager.
    Architecture supports future drop-in vector database (ChromaDB / FAISS)
    for semantic similarity search without changing the API.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = str(db_path or config.memory.DB_PATH)
        self._lock = threading.Lock()
        self._init_database()
        logger.info(f"MemoryManager initialized at: {self._db_path}")

    # -----------------------------------------------------------------------
    # Database Initialization
    # -----------------------------------------------------------------------

    def _init_database(self) -> None:
        """Create all required tables on first run."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    role        TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    timestamp   REAL NOT NULL,
                    session_id  TEXT
                );

                CREATE TABLE IF NOT EXISTS notes (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    title       TEXT,
                    content     TEXT NOT NULL,
                    tags        TEXT,
                    timestamp   REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reminders (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    title       TEXT NOT NULL,
                    due_time    REAL,
                    is_done     INTEGER DEFAULT 0,
                    created_at  REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS preferences (
                    key         TEXT PRIMARY KEY,
                    value       TEXT NOT NULL,
                    updated_at  REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS app_usage (
                    app_name    TEXT PRIMARY KEY,
                    launch_count INTEGER DEFAULT 1,
                    last_used   REAL NOT NULL
                );
            """)
        logger.debug("SARA memory database tables initialized.")

    def _get_conn(self) -> sqlite3.Connection:
        """Return a new SQLite connection (thread-safe)."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    # -----------------------------------------------------------------------
    # Conversation History
    # -----------------------------------------------------------------------

    def add_conversation_entry(self, role: str, content: str, session_id: Optional[str] = None) -> None:
        """Persist a single conversation turn (user or assistant message)."""
        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO conversations (role, content, timestamp, session_id) VALUES (?, ?, ?, ?)",
                    (role, content, time.time(), session_id)
                )
        logger.debug(f"Stored conversation [{role}]: '{content[:60]}...'")

    def get_conversation_history(self, limit: int = 20, session_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Retrieve recent conversation turns as OpenAI-compatible message list."""
        with self._get_conn() as conn:
            if session_id:
                rows = conn.execute(
                    "SELECT role, content FROM conversations WHERE session_id=? ORDER BY timestamp DESC LIMIT ?",
                    (session_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT role, content FROM conversations ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    # -----------------------------------------------------------------------
    # Notes & Reminders
    # -----------------------------------------------------------------------

    def save_note(self, content: str, title: Optional[str] = None, tags: Optional[List[str]] = None) -> int:
        """Save a user note or memory fact. Returns the note ID."""
        tag_str = json.dumps(tags) if tags else "[]"
        with self._lock:
            with self._get_conn() as conn:
                cur = conn.execute(
                    "INSERT INTO notes (title, content, tags, timestamp) VALUES (?, ?, ?, ?)",
                    (title, content, tag_str, time.time())
                )
                return cur.lastrowid

    def get_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent notes."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, content, tags, timestamp FROM notes ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def search_notes(self, keyword: str) -> List[Dict[str, Any]]:
        """Full-text keyword search across note titles and content."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, content, tags, timestamp FROM notes WHERE content LIKE ? OR title LIKE ? ORDER BY timestamp DESC",
                (f"%{keyword}%", f"%{keyword}%")
            ).fetchall()
        return [dict(r) for r in rows]

    def add_reminder(self, title: str, due_time: Optional[float] = None) -> int:
        """Create a reminder entry."""
        with self._lock:
            with self._get_conn() as conn:
                cur = conn.execute(
                    "INSERT INTO reminders (title, due_time, created_at) VALUES (?, ?, ?)",
                    (title, due_time, time.time())
                )
                return cur.lastrowid

    def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Return all reminders not yet marked as done."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, due_time, created_at FROM reminders WHERE is_done=0 ORDER BY due_time ASC"
            ).fetchall()
        return [dict(r) for r in rows]

    # -----------------------------------------------------------------------
    # User Preferences
    # -----------------------------------------------------------------------

    def set_preference(self, key: str, value: Any) -> None:
        """Store or update a user preference key-value pair."""
        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, ?)",
                    (key, json.dumps(value), time.time())
                )

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Retrieve a stored preference value."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT value FROM preferences WHERE key=?", (key,)).fetchone()
        if row:
            return json.loads(row["value"])
        return default

    # -----------------------------------------------------------------------
    # App Usage Tracking
    # -----------------------------------------------------------------------

    def log_app_usage(self, app_name: str) -> None:
        """Increment usage count and update last-used timestamp for an app."""
        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    """INSERT INTO app_usage (app_name, launch_count, last_used) VALUES (?, 1, ?)
                       ON CONFLICT(app_name) DO UPDATE SET launch_count=launch_count+1, last_used=excluded.last_used""",
                    (app_name.lower(), time.time())
                )

    def get_frequently_used_apps(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Return top N most frequently launched apps."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT app_name, launch_count, last_used FROM app_usage ORDER BY launch_count DESC LIMIT ?",
                (top_n,)
            ).fetchall()
        return [dict(r) for r in rows]
