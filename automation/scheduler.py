"""
SARA Task Scheduler
Background daemon that runs named tasks at defined times or intervals.
Persists scheduled tasks to SQLite so they survive restarts.

Supports:
  - One-shot tasks: "Shut down at 11 PM"
  - Recurring tasks: "Check battery every 30 minutes"
  - Cron-style tasks: "Open Spotify every weekday at 8 AM"
"""

import threading
import time
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Optional, List
from pathlib import Path
from config import config
from utils.logger import logger


class ScheduledTask:
    """Represents a single scheduled automation task."""

    def __init__(
        self,
        task_id: str,
        name: str,
        action: str,
        params: Dict[str, Any],
        trigger: str,          # "once" | "interval" | "daily" | "weekday"
        trigger_value: Any,    # seconds (interval) | "HH:MM" (daily) | list of weekdays
        enabled: bool = True,
    ):
        self.task_id = task_id
        self.name = name
        self.action = action
        self.params = params
        self.trigger = trigger
        self.trigger_value = trigger_value
        self.enabled = enabled
        self.last_run: Optional[float] = None
        self.run_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "action": self.action,
            "params": self.params,
            "trigger": self.trigger,
            "trigger_value": self.trigger_value,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "run_count": self.run_count,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ScheduledTask":
        task = cls(
            task_id=d["task_id"],
            name=d["name"],
            action=d["action"],
            params=d.get("params", {}),
            trigger=d["trigger"],
            trigger_value=d["trigger_value"],
            enabled=d.get("enabled", True),
        )
        task.last_run = d.get("last_run")
        task.run_count = d.get("run_count", 0)
        return task


class TaskScheduler:
    """
    Background thread scheduler for SARA automation tasks.
    Checks every 10 seconds for due tasks and fires the dispatch callback.
    """

    CHECK_INTERVAL = 10  # seconds

    def __init__(self, dispatch_callback: Callable[[str, Dict[str, Any]], None]):
        """
        Args:
            dispatch_callback: Called with (action: str, params: dict) when a task fires.
        """
        self._dispatch = dispatch_callback
        self._tasks: Dict[str, ScheduledTask] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._db_path = config.memory.DB_PATH
        self._load_from_db()
        logger.info(f"TaskScheduler initialized. {len(self._tasks)} task(s) loaded.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_task(self, task: ScheduledTask) -> None:
        """Register a new scheduled task and persist it."""
        with self._lock:
            self._tasks[task.task_id] = task
        self._save_to_db(task)
        logger.info(f"[Scheduler] Task added: '{task.name}' ({task.trigger}={task.trigger_value})")

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID."""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                self._delete_from_db(task_id)
                logger.info(f"[Scheduler] Task removed: {task_id}")
                return True
        return False

    def enable_task(self, task_id: str, enabled: bool = True) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].enabled = enabled
        self._update_enabled_in_db(task_id, enabled)

    def list_tasks(self) -> List[Dict[str, Any]]:
        """Return all tasks as list of dicts."""
        with self._lock:
            return [t.to_dict() for t in self._tasks.values()]

    def start(self) -> None:
        """Start the background scheduler thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            name="SARAScheduler",
            daemon=True
        )
        self._thread.start()
        logger.info("[Scheduler] Background scheduler started.")

    def stop(self) -> None:
        """Stop the scheduler loop gracefully."""
        self._running = False
        logger.info("[Scheduler] Stopped.")

    # ------------------------------------------------------------------
    # Scheduler Loop
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Main loop — checks for due tasks every CHECK_INTERVAL seconds."""
        while self._running:
            now = time.time()
            now_dt = datetime.fromtimestamp(now)
            with self._lock:
                due_tasks = [t for t in self._tasks.values() if t.enabled and self._is_due(t, now, now_dt)]

            for task in due_tasks:
                self._fire_task(task)

            time.sleep(self.CHECK_INTERVAL)

    def _is_due(self, task: ScheduledTask, now: float, now_dt: datetime) -> bool:
        """Return True if this task should fire right now."""
        if task.trigger == "once":
            # trigger_value is unix timestamp
            target = float(task.trigger_value)
            if task.last_run is None and now >= target:
                return True

        elif task.trigger == "interval":
            # trigger_value is interval in seconds
            interval = float(task.trigger_value)
            if task.last_run is None or (now - task.last_run) >= interval:
                return True

        elif task.trigger == "daily":
            # trigger_value is "HH:MM"
            target_h, target_m = map(int, task.trigger_value.split(":"))
            if now_dt.hour == target_h and now_dt.minute == target_m:
                # Only fire once per minute — check last_run isn't within this minute
                if task.last_run is None or (now - task.last_run) >= 60:
                    return True

        elif task.trigger == "weekday":
            # trigger_value is {"time": "HH:MM", "days": [0,1,2,3,4]}  (0=Mon)
            cfg = task.trigger_value if isinstance(task.trigger_value, dict) else json.loads(task.trigger_value)
            if now_dt.weekday() in cfg.get("days", []):
                target_h, target_m = map(int, cfg["time"].split(":"))
                if now_dt.hour == target_h and now_dt.minute == target_m:
                    if task.last_run is None or (now - task.last_run) >= 60:
                        return True

        return False

    def _fire_task(self, task: ScheduledTask) -> None:
        """Execute a due task via the dispatch callback."""
        logger.info(f"[Scheduler] Firing task: '{task.name}' (action={task.action})")
        task.last_run = time.time()
        task.run_count += 1

        # Remove one-shot tasks after firing
        if task.trigger == "once":
            with self._lock:
                self._tasks.pop(task.task_id, None)
            self._delete_from_db(task.task_id)

        try:
            self._dispatch(task.action, task.params)
        except Exception as e:
            logger.error(f"[Scheduler] Task '{task.name}' dispatch failed: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # SQLite Persistence
    # ------------------------------------------------------------------

    def _ensure_table(self, conn: sqlite3.Connection) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                task_id       TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                action        TEXT NOT NULL,
                params        TEXT,
                trigger_type  TEXT NOT NULL,
                trigger_value TEXT,
                enabled       INTEGER DEFAULT 1,
                last_run      REAL,
                run_count     INTEGER DEFAULT 0
            )
        """)

    def _load_from_db(self) -> None:
        try:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._ensure_table(conn)
            rows = conn.execute("SELECT * FROM scheduled_tasks WHERE enabled=1").fetchall()
            conn.close()
            for row in rows:
                task = ScheduledTask(
                    task_id=row["task_id"],
                    name=row["name"],
                    action=row["action"],
                    params=json.loads(row["params"] or "{}"),
                    trigger=row["trigger_type"],
                    trigger_value=row["trigger_value"],
                    enabled=bool(row["enabled"]),
                )
                task.last_run = row["last_run"]
                task.run_count = row["run_count"] or 0
                self._tasks[task.task_id] = task
        except Exception as e:
            logger.error(f"[Scheduler] DB load error: {e}", exc_info=True)

    def _save_to_db(self, task: ScheduledTask) -> None:
        try:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._ensure_table(conn)
            conn.execute("""
                INSERT OR REPLACE INTO scheduled_tasks
                (task_id, name, action, params, trigger_type, trigger_value, enabled, last_run, run_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.task_id, task.name, task.action,
                json.dumps(task.params),
                task.trigger,
                json.dumps(task.trigger_value) if isinstance(task.trigger_value, (dict, list)) else str(task.trigger_value),
                int(task.enabled), task.last_run, task.run_count
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[Scheduler] DB save error: {e}", exc_info=True)

    def _delete_from_db(self, task_id: str) -> None:
        try:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._ensure_table(conn)
            conn.execute("DELETE FROM scheduled_tasks WHERE task_id=?", (task_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[Scheduler] DB delete error: {e}", exc_info=True)

    def _update_enabled_in_db(self, task_id: str, enabled: bool) -> None:
        try:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._ensure_table(conn)
            conn.execute("UPDATE scheduled_tasks SET enabled=? WHERE task_id=?", (int(enabled), task_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[Scheduler] DB update error: {e}", exc_info=True)
