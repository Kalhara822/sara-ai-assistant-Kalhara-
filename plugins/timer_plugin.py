"""
System Timer & Countdown Plugin for SARA AI Assistant
Handles: shutdown_timer, set_timer, cancel_timer, list_timers
Drop this file into plugins/ — SARA auto-loads it.
"""

import threading
import time
import subprocess
from typing import Dict, Any, List, Optional
from plugins.base import BasePlugin
from utils.logger import logger


class TimerPlugin(BasePlugin):
    """
    Timer Plugin — manages countdown timers, scheduled shutdowns, and reminders.
    Supports: set_timer, cancel_timer, list_timers, shutdown_after actions.
    """

    def __init__(self):
        self._timers: Dict[str, threading.Timer] = {}
        self._timer_meta: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    @property
    def plugin_name(self) -> str:
        return "TimerPlugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_actions(self) -> List[str]:
        return ["set_timer", "cancel_timer", "list_timers", "shutdown_after"]

    def initialize(self) -> bool:
        logger.info("[TimerPlugin] Initialized.")
        return True

    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "set_timer":
            return self._set_timer(params)
        elif action == "cancel_timer":
            return self._cancel_timer(params)
        elif action == "list_timers":
            return self._list_timers()
        elif action == "shutdown_after":
            return self._shutdown_after(params)
        return {"status": "error", "message": f"Unknown action: {action}"}

    # ------------------------------------------------------------------

    def _set_timer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set a countdown timer with an optional label."""
        seconds = self._parse_seconds(params)
        if seconds <= 0:
            return {"status": "error", "message": "Please specify a valid timer duration (e.g. '5 minutes')."}

        label = str(params.get("query") or f"Timer-{int(time.time())}")
        timer_id = f"timer_{int(time.time())}"

        def _fire():
            with self._lock:
                self._timers.pop(timer_id, None)
                self._timer_meta.pop(timer_id, None)
            logger.info(f"[TimerPlugin] Timer fired: '{label}'")
            # On-screen notification via Windows toast (fallback: log)
            try:
                subprocess.Popen(
                    f'powershell -command "Add-Type -AssemblyName System.Windows.Forms; '
                    f'[System.Windows.Forms.MessageBox]::Show(\'Timer: {label} has ended!\', \'SARA Timer\')"',
                    shell=True
                )
            except Exception:
                pass

        timer = threading.Timer(seconds, _fire)
        timer.daemon = True
        timer.start()

        with self._lock:
            self._timers[timer_id] = timer
            self._timer_meta[timer_id] = {
                "label": label,
                "seconds": seconds,
                "started_at": time.time(),
                "ends_at": time.time() + seconds,
            }

        mins, secs = divmod(int(seconds), 60)
        duration_str = f"{mins} minute{'s' if mins != 1 else ''}" if mins else f"{secs} second{'s' if secs != 1 else ''}"
        return {"status": "success", "message": f"Timer set for {duration_str}: '{label}'."}

    def _cancel_timer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel the most recent or named timer."""
        with self._lock:
            if not self._timers:
                return {"status": "success", "message": "No active timers to cancel."}
            # Cancel the most recently added timer
            timer_id = list(self._timers.keys())[-1]
            label = self._timer_meta.get(timer_id, {}).get("label", timer_id)
            self._timers[timer_id].cancel()
            self._timers.pop(timer_id)
            self._timer_meta.pop(timer_id)
        return {"status": "success", "message": f"Timer cancelled: '{label}'."}

    def _list_timers(self) -> Dict[str, Any]:
        """List all currently active timers."""
        with self._lock:
            if not self._timer_meta:
                return {"status": "success", "message": "No active timers running."}
            now = time.time()
            entries = []
            for tid, meta in self._timer_meta.items():
                remaining = max(0, meta["ends_at"] - now)
                mins, secs = divmod(int(remaining), 60)
                entries.append(f"'{meta['label']}' ({mins}m {secs}s remaining)")
            summary = "; ".join(entries)
        return {"status": "success", "message": f"Active timers: {summary}", "data": list(self._timer_meta.values())}

    def _shutdown_after(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a Windows shutdown after N seconds/minutes."""
        seconds = self._parse_seconds(params)
        if seconds <= 0:
            return {"status": "error", "message": "Please specify how long before shutdown (e.g. '10 minutes')."}
        try:
            subprocess.run(f"shutdown /s /t {int(seconds)}", shell=True, check=True)
            mins = int(seconds // 60)
            return {"status": "success", "message": f"System will shut down in {mins} minute{'s' if mins != 1 else ''}."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def _parse_seconds(params: Dict[str, Any]) -> float:
        """Parse duration from params into seconds."""
        value = params.get("value")
        if value is None:
            return 0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0
