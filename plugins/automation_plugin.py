"""
Automation Plugin for SARA AI Assistant
Exposes Routines, Scheduler, and File Organizer as voice/text commands.
Drop this file into plugins/ — SARA auto-loads it.

Supported actions:
  run_routine, list_routines, create_routine
  schedule_task, list_scheduled_tasks, cancel_scheduled_task
  organize_downloads, find_large_files, clean_temp, archive_old_files
"""

import uuid
import time
from typing import Dict, Any, List
from plugins.base import BasePlugin
from utils.logger import logger

# Lazy imports to avoid circular issues — instantiated in initialize()
_routine_engine = None
_scheduler = None
_file_organizer = None


class AutomationPlugin(BasePlugin):
    """
    Master Automation Plugin — routines, scheduling, file management.
    Requires: automation/routines.py, automation/scheduler.py, automation/file_organizer.py
    """

    @property
    def plugin_name(self) -> str:
        return "AutomationPlugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_actions(self) -> List[str]:
        return [
            "run_routine", "list_routines", "create_routine",
            "schedule_task", "list_scheduled_tasks", "cancel_scheduled_task",
            "organize_downloads", "find_large_files",
            "clean_temp", "archive_old_files",
        ]

    def initialize(self) -> bool:
        global _routine_engine, _scheduler, _file_organizer
        try:
            from automation.routines import RoutineEngine
            from automation.scheduler import TaskScheduler, ScheduledTask
            from automation.file_organizer import FileOrganizer

            def _dispatch_action(action: str, params: Dict[str, Any]):
                """Internal dispatcher used by scheduler/routine engine."""
                # We don't have direct access to the main dispatcher here,
                # so we import and call SARAEngine indirectly via a thread-safe ref.
                # The engine will be set via set_engine() after SARAEngine is ready.
                if self._engine_ref:
                    self._engine_ref.process_command_direct(action, params)

            self._engine_ref = None
            _routine_engine = RoutineEngine(dispatch_callback=_dispatch_action)
            _scheduler = TaskScheduler(dispatch_callback=_dispatch_action)
            _scheduler.start()
            _file_organizer = FileOrganizer()

            logger.info("[AutomationPlugin] Routines, Scheduler, FileOrganizer initialized.")
            return True
        except Exception as e:
            logger.error(f"[AutomationPlugin] Initialization failed: {e}", exc_info=True)
            return False

    def set_engine(self, engine) -> None:
        """Called by SARAEngine after init to wire back the dispatcher."""
        self._engine_ref = engine

    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "run_routine":
            return self._run_routine(params)
        elif action == "list_routines":
            return self._list_routines()
        elif action == "create_routine":
            return self._create_routine(params)
        elif action == "schedule_task":
            return self._schedule_task(params)
        elif action == "list_scheduled_tasks":
            return self._list_scheduled_tasks()
        elif action == "cancel_scheduled_task":
            return self._cancel_scheduled_task(params)
        elif action == "organize_downloads":
            return _file_organizer.organize_downloads()
        elif action == "find_large_files":
            folder = params.get("query", "C:/Users")
            return _file_organizer.find_large_files(folder)
        elif action == "clean_temp":
            return _file_organizer.clean_temp_files()
        elif action == "archive_old_files":
            folder = params.get("query", "")
            days = int(params.get("value", 90))
            if not folder:
                return {"status": "error", "message": "Please specify which folder to archive."}
            return _file_organizer.archive_old_files(folder, days)
        return {"status": "error", "message": f"Unknown automation action: {action}"}

    # ------------------------------------------------------------------

    def _run_routine(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("query") or params.get("value") or ""
        if not name:
            return {"status": "error", "message": "Please specify which routine to run."}
        return _routine_engine.run_routine(str(name))

    def _list_routines(self) -> Dict[str, Any]:
        routines = _routine_engine.list_routines()
        if not routines:
            return {"status": "success", "message": "No routines defined yet."}
        names = ", ".join([f"'{r['name']}'" for r in routines])
        return {
            "status": "success",
            "message": f"Available routines: {names}.",
            "data": routines,
        }

    def _create_routine(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("query") or params.get("value") or ""
        steps = params.get("steps", [])
        if not name:
            return {"status": "error", "message": "Please provide a name for the routine."}
        if not steps:
            return {"status": "error", "message": "No steps defined for the routine."}
        return _routine_engine.create_routine(name, steps)

    def _schedule_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        from automation.scheduler import ScheduledTask
        action = params.get("action_to_schedule", "")
        trigger = params.get("trigger", "interval")
        trigger_value = params.get("trigger_value", 3600)
        name = params.get("name", f"Task-{int(time.time())}")
        task_params = params.get("task_params", {})

        if not action:
            return {"status": "error", "message": "Please specify what action to schedule."}

        task = ScheduledTask(
            task_id=str(uuid.uuid4()),
            name=name,
            action=action,
            params=task_params,
            trigger=trigger,
            trigger_value=trigger_value,
        )
        _scheduler.add_task(task)
        return {"status": "success", "message": f"Scheduled task '{name}' created."}

    def _list_scheduled_tasks(self) -> Dict[str, Any]:
        tasks = _scheduler.list_tasks()
        if not tasks:
            return {"status": "success", "message": "No scheduled tasks configured."}
        names = ", ".join([f"'{t['name']}'" for t in tasks[:5]])
        return {"status": "success", "message": f"Scheduled tasks: {names}.", "data": tasks}

    def _cancel_scheduled_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task_id = params.get("query") or params.get("value") or ""
        if not task_id:
            return {"status": "error", "message": "Please specify the task ID or name to cancel."}
        # Try by ID first, then by name
        tasks = _scheduler.list_tasks()
        match = next((t for t in tasks if t["task_id"] == task_id or t["name"] == task_id), None)
        if match:
            _scheduler.remove_task(match["task_id"])
            return {"status": "success", "message": f"Task '{match['name']}' cancelled."}
        return {"status": "not_found", "message": f"No task found with id/name: '{task_id}'."}
