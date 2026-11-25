"""
SARA Smart Routines Engine
Defines named multi-step routines that execute sequences of commands.

Built-in routines:
  - "morning"     : Volume up, check weather, open browser, greet user
  - "work"        : Open VS Code, Chrome, set volume to 50, set brightness to 80
  - "night"       : Volume down, dim brightness, lock PC in 5 min
  - "dev setup"   : Open VS Code + Chrome + Terminal
  - "presentation": Set volume to 30, brightness max, open PowerPoint

Users can define custom routines via voice: "Sara, create a routine called..."
Custom routines are persisted to SQLite.
"""

import time
import json
import sqlite3
import uuid
from typing import Dict, Any, List, Callable, Optional
from config import config
from utils.logger import logger


class RoutineStep:
    """A single step in a routine — one action with params."""

    def __init__(self, action: str, params: Dict[str, Any] = None, delay_after: float = 0.5):
        self.action = action
        self.params = params or {}
        self.delay_after = delay_after  # seconds to wait after this step

    def to_dict(self) -> Dict[str, Any]:
        return {"action": self.action, "params": self.params, "delay_after": self.delay_after}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RoutineStep":
        return cls(d["action"], d.get("params", {}), d.get("delay_after", 0.5))


class Routine:
    """A named sequence of RoutineSteps."""

    def __init__(self, routine_id: str, name: str, steps: List[RoutineStep], description: str = ""):
        self.routine_id = routine_id
        self.name = name.lower().strip()
        self.steps = steps
        self.description = description
        self.is_builtin = False
        self.run_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "routine_id": self.routine_id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "is_builtin": self.is_builtin,
            "run_count": self.run_count,
        }


class RoutineEngine:
    """
    Manages built-in and custom routines.
    Executes multi-step command sequences with delays between steps.
    """

    def __init__(self, dispatch_callback: Callable[[str, Dict[str, Any]], None]):
        """
        Args:
            dispatch_callback: Function(action, params) that executes a command.
        """
        self._dispatch = dispatch_callback
        self._routines: Dict[str, Routine] = {}
        self._db_path = config.memory.DB_PATH
        self._register_builtins()
        self._load_custom_routines()
        logger.info(f"RoutineEngine initialized. {len(self._routines)} routine(s) available.")

    # ------------------------------------------------------------------
    # Built-in Routines
    # ------------------------------------------------------------------

    def _register_builtins(self) -> None:
        """Register all pre-defined smart routines."""
        builtins = [
            Routine(
                routine_id="morning",
                name="morning",
                description="Good morning startup: weather, volume up, open browser",
                steps=[
                    RoutineStep("increase_volume", {}, delay_after=0.3),
                    RoutineStep("set_brightness", {"value": 80}, delay_after=0.3),
                    RoutineStep("check_weather", {}, delay_after=1.0),
                    RoutineStep("open_application", {"application": "chrome"}, delay_after=1.0),
                ],
            ),
            Routine(
                routine_id="work",
                name="work",
                description="Work mode: VS Code + Chrome, focus settings",
                steps=[
                    RoutineStep("set_volume", {"value": 40}, delay_after=0.3),
                    RoutineStep("set_brightness", {"value": 75}, delay_after=0.3),
                    RoutineStep("open_application", {"application": "vs code"}, delay_after=1.5),
                    RoutineStep("open_application", {"application": "chrome"}, delay_after=1.0),
                ],
            ),
            Routine(
                routine_id="night",
                name="night",
                description="Night mode: dim screen, lower volume",
                steps=[
                    RoutineStep("set_volume", {"value": 20}, delay_after=0.3),
                    RoutineStep("set_brightness", {"value": 30}, delay_after=0.3),
                ],
            ),
            Routine(
                routine_id="dev_setup",
                name="dev setup",
                description="Developer setup: VS Code + Chrome + PowerShell",
                steps=[
                    RoutineStep("open_application", {"application": "vs code"}, delay_after=2.0),
                    RoutineStep("open_application", {"application": "chrome"}, delay_after=1.5),
                    RoutineStep("open_application", {"application": "powershell"}, delay_after=1.0),
                    RoutineStep("set_volume", {"value": 50}, delay_after=0.2),
                    RoutineStep("set_brightness", {"value": 80}, delay_after=0.2),
                ],
            ),
            Routine(
                routine_id="presentation",
                name="presentation",
                description="Presentation mode: max brightness, low volume",
                steps=[
                    RoutineStep("set_brightness", {"value": 100}, delay_after=0.3),
                    RoutineStep("set_volume", {"value": 25}, delay_after=0.3),
                    RoutineStep("open_application", {"application": "powerpoint"}, delay_after=1.5),
                ],
            ),
            Routine(
                routine_id="lock_and_go",
                name="lock and go",
                description="Save everything and lock the PC",
                steps=[
                    RoutineStep("take_screenshot", {}, delay_after=0.5),
                    RoutineStep("lock_pc", {}, delay_after=0.0),
                ],
            ),
            Routine(
                routine_id="focus",
                name="focus",
                description="Focus mode: mute audio, high brightness",
                steps=[
                    RoutineStep("mute_volume", {}, delay_after=0.3),
                    RoutineStep("set_brightness", {"value": 90}, delay_after=0.3),
                ],
            ),
        ]

        for r in builtins:
            r.is_builtin = True
            self._routines[r.name] = r

        logger.debug(f"Registered {len(builtins)} built-in routines.")

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_routine(self, name: str) -> Dict[str, Any]:
        """Execute a routine by name. Returns result summary."""
        name = name.lower().strip()
        routine = self._routines.get(name)
        if not routine:
            # Fuzzy match — try partial name
            matches = [r for rn, r in self._routines.items() if name in rn]
            if matches:
                routine = matches[0]
            else:
                available = ", ".join(f"'{n}'" for n in self._routines.keys())
                return {
                    "status": "not_found",
                    "message": f"No routine named '{name}'. Available: {available}"
                }

        logger.info(f"[RoutineEngine] Running routine: '{routine.name}' ({len(routine.steps)} steps)")
        routine.run_count += 1
        errors = []

        for i, step in enumerate(routine.steps, 1):
            logger.debug(f"  Step {i}/{len(routine.steps)}: {step.action} {step.params}")
            try:
                self._dispatch(step.action, step.params)
            except Exception as e:
                errors.append(f"Step {i} ({step.action}): {e}")
                logger.warning(f"[RoutineEngine] Step failed: {e}")

            if step.delay_after > 0:
                time.sleep(step.delay_after)

        status = "success" if not errors else "partial"
        msg = f"Routine '{routine.name}' completed ({len(routine.steps)} steps)."
        if errors:
            msg += f" {len(errors)} step(s) encountered errors."

        return {"status": status, "message": msg, "errors": errors}

    # ------------------------------------------------------------------
    # Custom Routines (CRUD)
    # ------------------------------------------------------------------

    def create_routine(self, name: str, steps: List[Dict[str, Any]], description: str = "") -> Dict[str, Any]:
        """Create and persist a user-defined custom routine."""
        name = name.lower().strip()
        if name in self._routines and self._routines[name].is_builtin:
            return {"status": "error", "message": f"Cannot overwrite built-in routine '{name}'."}

        routine = Routine(
            routine_id=str(uuid.uuid4()),
            name=name,
            steps=[RoutineStep.from_dict(s) for s in steps],
            description=description,
        )
        self._routines[name] = routine
        self._save_custom_routine(routine)
        logger.info(f"[RoutineEngine] Custom routine created: '{name}'")
        return {"status": "success", "message": f"Routine '{name}' created with {len(steps)} steps."}

    def delete_routine(self, name: str) -> Dict[str, Any]:
        """Delete a user-defined routine."""
        name = name.lower().strip()
        routine = self._routines.get(name)
        if not routine:
            return {"status": "not_found", "message": f"No routine named '{name}'."}
        if routine.is_builtin:
            return {"status": "error", "message": f"Cannot delete built-in routine '{name}'."}
        del self._routines[name]
        self._delete_custom_routine(routine.routine_id)
        return {"status": "success", "message": f"Routine '{name}' deleted."}

    def list_routines(self) -> List[Dict[str, Any]]:
        """Return all routines as summary dicts."""
        return [
            {
                "name": r.name,
                "description": r.description,
                "steps": len(r.steps),
                "is_builtin": r.is_builtin,
                "run_count": r.run_count,
            }
            for r in self._routines.values()
        ]

    # ------------------------------------------------------------------
    # SQLite Persistence
    # ------------------------------------------------------------------

    def _ensure_table(self, conn: sqlite3.Connection) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_routines (
                routine_id  TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                description TEXT,
                steps       TEXT NOT NULL,
                run_count   INTEGER DEFAULT 0
            )
        """)

    def _load_custom_routines(self) -> None:
        try:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._ensure_table(conn)
            rows = conn.execute("SELECT * FROM custom_routines").fetchall()
            conn.close()
            for row in rows:
                steps = [RoutineStep.from_dict(s) for s in json.loads(row["steps"])]
                r = Routine(row["routine_id"], row["name"], steps, row["description"] or "")
                r.run_count = row["run_count"] or 0
                self._routines[r.name] = r
            if rows:
                logger.info(f"[RoutineEngine] Loaded {len(rows)} custom routine(s) from DB.")
        except Exception as e:
            logger.error(f"[RoutineEngine] DB load error: {e}", exc_info=True)

    def _save_custom_routine(self, routine: Routine) -> None:
        try:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._ensure_table(conn)
            conn.execute("""
                INSERT OR REPLACE INTO custom_routines (routine_id, name, description, steps, run_count)
                VALUES (?, ?, ?, ?, ?)
            """, (routine.routine_id, routine.name, routine.description,
                  json.dumps([s.to_dict() for s in routine.steps]), routine.run_count))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[RoutineEngine] DB save error: {e}", exc_info=True)

    def _delete_custom_routine(self, routine_id: str) -> None:
        try:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._ensure_table(conn)
            conn.execute("DELETE FROM custom_routines WHERE routine_id=?", (routine_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[RoutineEngine] DB delete error: {e}", exc_info=True)
