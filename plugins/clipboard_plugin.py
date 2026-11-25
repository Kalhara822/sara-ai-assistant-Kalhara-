"""
Clipboard Manager Plugin for SARA AI Assistant
Provides clipboard read/write/history/search via Windows clipboard API.
Drop this file into plugins/ — SARA auto-loads it.
"""

import time
from typing import Dict, Any, List, Deque
from collections import deque
from plugins.base import BasePlugin
from utils.logger import logger

try:
    import tkinter as tk
    HAS_TK = True
except ImportError:
    HAS_TK = False

try:
    import win32clipboard
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class ClipboardManagerPlugin(BasePlugin):
    """
    Clipboard Manager Plugin — reads/writes/tracks clipboard history.
    Supports: clipboard_copy, clipboard_paste, clipboard_history actions.
    """

    MAX_HISTORY = 20  # Keep last 20 clipboard entries

    def __init__(self):
        self._history: Deque[Dict[str, Any]] = deque(maxlen=self.MAX_HISTORY)

    @property
    def plugin_name(self) -> str:
        return "ClipboardManagerPlugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_actions(self) -> List[str]:
        return ["clipboard_copy", "clipboard_paste", "clipboard_history"]

    def initialize(self) -> bool:
        if not HAS_TK and not HAS_WIN32:
            logger.warning("[ClipboardPlugin] No clipboard backend available.")
            return False
        logger.info("[ClipboardPlugin] Initialized.")
        return True

    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "clipboard_copy":
            return self._copy_to_clipboard(params)
        elif action == "clipboard_paste":
            return self._read_from_clipboard()
        elif action == "clipboard_history":
            return self._get_history()
        return {"status": "error", "message": f"Unknown action: {action}"}

    # ------------------------------------------------------------------

    def _copy_to_clipboard(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Copy text content to Windows clipboard."""
        text = str(params.get("query") or params.get("value") or "")
        if not text:
            return {"status": "error", "message": "No text provided to copy."}
        try:
            if HAS_WIN32:
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
            else:
                root = tk.Tk()
                root.withdraw()
                root.clipboard_clear()
                root.clipboard_append(text)
                root.update()
                root.destroy()

            self._history.appendleft({"text": text, "timestamp": time.time(), "action": "copy"})
            preview = text[:40] + "..." if len(text) > 40 else text
            logger.info(f"[ClipboardPlugin] Copied: '{preview}'")
            return {"status": "success", "message": f"Copied to clipboard: '{preview}'"}
        except Exception as e:
            logger.error(f"[ClipboardPlugin] Copy error: {e}")
            return {"status": "error", "message": str(e)}

    def _read_from_clipboard(self) -> Dict[str, Any]:
        """Read current clipboard content."""
        try:
            if HAS_WIN32:
                win32clipboard.OpenClipboard()
                text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
            else:
                root = tk.Tk()
                root.withdraw()
                text = root.clipboard_get()
                root.destroy()

            self._history.appendleft({"text": text, "timestamp": time.time(), "action": "paste"})
            preview = text[:80] + "..." if len(text) > 80 else text
            return {"status": "success", "message": f"Clipboard contains: '{preview}'", "data": text}
        except Exception as e:
            logger.error(f"[ClipboardPlugin] Paste error: {e}")
            return {"status": "error", "message": "Clipboard is empty or contains non-text content."}

    def _get_history(self) -> Dict[str, Any]:
        """Return recent clipboard history entries."""
        if not self._history:
            return {"status": "success", "message": "Clipboard history is empty."}
        items = list(self._history)[:5]
        summary = "; ".join([f"'{i['text'][:30]}'" for i in items])
        return {
            "status": "success",
            "message": f"Last {len(items)} clipboard entries: {summary}",
            "data": items
        }
