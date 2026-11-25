"""
Universal Windows Application Launcher & Process Manager
Scans Windows Start Menu & AppX packages (via Get-StartApps) to open ANY installed application
(WhatsApp, Chrome, Telegram, VS Code, Office, Zoom, CapCut, Calculator, Settings, etc.).
"""

import os
import sys
import json
import threading
import subprocess
import psutil
from typing import Dict, Any, List, Optional
from commands.base import BaseCommand
from utils.logger import logger

# Static fallback shortcuts for standard Windows utilities
APP_MAP: Dict[str, Dict[str, str]] = {
    "chrome":       {"exe": "chrome.exe",         "launch": "start chrome"},
    "google chrome":{"exe": "chrome.exe",         "launch": "start chrome"},
    "firefox":      {"exe": "firefox.exe",        "launch": "start firefox"},
    "edge":         {"exe": "msedge.exe",         "launch": "start msedge"},
    "vs code":      {"exe": "Code.exe",           "launch": "code"},
    "vscode":       {"exe": "Code.exe",           "launch": "code"},
    "code":         {"exe": "Code.exe",           "launch": "code"},
    "intellij":     {"exe": "idea64.exe",         "launch": "idea64"},
    "notepad":      {"exe": "notepad.exe",        "launch": "notepad"},
    "notepad++":    {"exe": "notepad++.exe",      "launch": "notepad++"},
    "calculator":   {"exe": "CalculatorApp.exe",  "launch": "calc"},
    "explorer":     {"exe": "explorer.exe",       "launch": "explorer"},
    "word":         {"exe": "WINWORD.EXE",        "launch": "start winword"},
    "excel":        {"exe": "EXCEL.EXE",          "launch": "start excel"},
    "powerpoint":   {"exe": "POWERPNT.EXE",       "launch": "start powerpnt"},
    "vlc":          {"exe": "vlc.exe",            "launch": "start vlc"},
    "task manager": {"exe": "Taskmgr.exe",        "launch": "taskmgr"},
    "cmd":          {"exe": "cmd.exe",            "launch": "start cmd"},
    "powershell":   {"exe": "powershell.exe",     "launch": "start powershell"},
}


class WindowsAppIndexer:
    """Background indexer that maps all installed Windows apps via Get-StartApps."""

    def __init__(self):
        self._apps_cache: List[Dict[str, str]] = []
        self._loaded_event = threading.Event()
        self._lock = threading.Lock()
        # Start background indexing immediately
        threading.Thread(target=self._index_apps, name="AppIndexer", daemon=True).start()

    def _index_apps(self):
        """Query PowerShell Get-StartApps and store in cache."""
        try:
            cmd = 'powershell -Command "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json -Depth 2"'
            output = subprocess.check_output(cmd, shell=True, timeout=20).decode('utf-8', errors='ignore')
            data = json.loads(output)
            with self._lock:
                if isinstance(data, list):
                    self._apps_cache = data
                elif isinstance(data, dict):
                    self._apps_cache = [data]
            logger.info(f"[AppIndexer] Discovered {len(self._apps_cache)} installed Windows applications.")
        except Exception as e:
            logger.warning(f"[AppIndexer] Could not index Windows apps via Get-StartApps: {e}")
        finally:
            self._loaded_event.set()

    def wait_until_loaded(self, timeout: float = 3.0) -> bool:
        """Wait for indexer to complete startup indexing."""
        return self._loaded_event.wait(timeout)

    def find_app_id(self, query: str) -> Optional[Dict[str, str]]:
        """Find matching app entry by name (exact or substring)."""
        self.wait_until_loaded(timeout=2.0)
        q = query.lower().strip()

        with self._lock:
            # 1. Exact match on Name
            for item in self._apps_cache:
                name = str(item.get("Name", "")).lower()
                if name == q:
                    return item

            # 2. Word boundary / startswith match
            for item in self._apps_cache:
                name = str(item.get("Name", "")).lower()
                if name.startswith(q) or q in name:
                    return item

        return None


# Global indexer instance
_indexer = WindowsAppIndexer()


class OpenApplicationCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "open_application"

    @property
    def description(self) -> str:
        return "Launch any named application on Windows (WhatsApp, Chrome, Word, VS Code, Zoom, etc.)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        app = str(params.get("application", "")).lower().strip()
        if not app or app in ["and lower guide", "lower guide", "and"]:
            return {"status": "error", "message": "Please specify an application name to open (e.g. 'Open WhatsApp')."}

        # Clean noise words ("the", "app", "application")
        app_clean = app.replace("the ", "").replace(" app", "").replace(" application", "").strip()

        # 1. Primary: Search Windows StartApps index FIRST (WhatsApp, UWP & Desktop Apps)
        matched_app = _indexer.find_app_id(app_clean)
        if matched_app:
            app_id = matched_app.get("AppID", "")
            app_name = matched_app.get("Name", app_clean.title())
            try:
                # Use explorer.exe shell:AppsFolder for clean UWP and Desktop App launching
                subprocess.Popen(f'explorer.exe shell:AppsFolder\\"{app_id}"', shell=True)
                logger.info(f"Launched application via shell:AppsFolder ({app_name}): {app_id}")
                return {"status": "success", "message": f"Opening {app_name}."}
            except Exception as e:
                logger.warning(f"StartApps launch failed for {app_name}: {e}")

        # 2. Secondary: Try APP_MAP static shortcuts
        app_info = APP_MAP.get(app_clean) or APP_MAP.get(app)
        if app_info:
            try:
                subprocess.Popen(app_info["launch"], shell=True)
                logger.info(f"Launched application (APP_MAP): {app_clean}")
                return {"status": "success", "message": f"Opening {app_clean.title()}."}
            except Exception as e:
                logger.warning(f"APP_MAP launch failed for {app_clean}: {e}")

        # 3. Fallback: Generic Windows 'start' shell launcher
        try:
            subprocess.Popen(f'start "" "{app_clean}"', shell=True)
            logger.info(f"Attempted generic shell start for: '{app_clean}'")
            return {"status": "success", "message": f"Opening {app_clean.title()}."}
        except Exception as e:
            logger.error(f"Failed to launch '{app_clean}': {e}")
            return {"status": "error", "message": f"Could not find or open '{app_clean}' on your computer."}


class CloseApplicationCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "close_application"

    @property
    def description(self) -> str:
        return "Terminate a running application process."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        app = str(params.get("application", "")).lower().strip()
        app_clean = app.replace("the ", "").replace(" app", "").replace(" application", "").strip()

        app_info = APP_MAP.get(app_clean)
        exe_name = app_info["exe"] if app_info else f"{app_clean}.exe"

        killed = False
        for proc in psutil.process_iter(["name", "pid"]):
            p_name = proc.info["name"]
            if p_name and (p_name.lower() == exe_name.lower() or app_clean in p_name.lower()):
                try:
                    proc.terminate()
                    killed = True
                    logger.info(f"Terminated process: {p_name}")
                except Exception as e:
                    logger.warning(f"Could not terminate {p_name}: {e}")

        if killed:
            return {"status": "success", "message": f"Closed {app_clean.title()}."}
        return {"status": "not_found", "message": f"'{app_clean.title()}' does not appear to be running."}
