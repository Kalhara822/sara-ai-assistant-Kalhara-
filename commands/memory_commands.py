"""
Memory Commands (Remember / Recall)
Handles: remember_note, recall_memory, set_reminder
"""

from typing import Dict, Any
from commands.base import BaseCommand
from database.memory_manager import MemoryManager
from utils.logger import logger

_memory = MemoryManager()


class RememberNoteCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "remember_note"

    @property
    def description(self) -> str:
        return "Save a note or piece of information to SARA's memory."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        content = params.get("query") or params.get("value") or ""
        if not content:
            return {"status": "error", "message": "Nothing to remember. Please specify the content."}
        note_id = _memory.save_note(content=str(content))
        logger.info(f"Note saved (id={note_id}): '{content[:60]}'")
        return {"status": "success", "message": f"Got it! I'll remember: '{content}'."}


class RecallMemoryCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "recall_memory"

    @property
    def description(self) -> str:
        return "Retrieve stored notes or recent memory from SARA's database."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        keyword = params.get("query", "").strip()
        if keyword:
            results = _memory.search_notes(keyword)
        else:
            results = _memory.get_notes(limit=5)

        if not results:
            return {"status": "success", "message": "I don't have any matching memories stored."}

        notes_text = "; ".join([r["content"][:80] for r in results[:3]])
        return {
            "status": "success",
            "message": f"Here's what I remember: {notes_text}",
            "data": results
        }


class SetReminderCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "set_reminder"

    @property
    def description(self) -> str:
        return "Set a new reminder."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        title = params.get("query") or params.get("value") or ""
        if not title:
            return {"status": "error", "message": "Please specify what to remind you about."}
        reminder_id = _memory.add_reminder(title=str(title))
        return {"status": "success", "message": f"Reminder set: '{title}'."}
