"""
System Control Commands
Handles: shutdown, restart, sleep, lock PC, screenshot, recycle bin
"""

import os
import subprocess
import time
from typing import Dict, Any
from commands.base import BaseCommand
from utils.logger import logger

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

try:
    import ctypes
    HAS_CTYPES = True
except ImportError:
    HAS_CTYPES = False


class ScreenshotCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "take_screenshot"

    @property
    def description(self) -> str:
        return "Capture a screenshot and save it to the Desktop."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filename = f"sara_screenshot_{int(time.time())}.png"
            filepath = os.path.join(desktop, filename)
            if HAS_PYAUTOGUI:
                screenshot = pyautogui.screenshot()
                screenshot.save(filepath)
                logger.info(f"Screenshot saved: {filepath}")
                return {"status": "success", "message": f"Screenshot saved to Desktop as {filename}."}
            else:
                return {"status": "error", "message": "pyautogui not available."}
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return {"status": "error", "message": str(e)}


class LockPCCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "lock_pc"

    @property
    def description(self) -> str:
        return "Lock the Windows user session."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if HAS_CTYPES:
                ctypes.windll.user32.LockWorkStation()
                return {"status": "success", "message": "PC locked."}
            else:
                subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
                return {"status": "success", "message": "PC locked."}
        except Exception as e:
            logger.error(f"Lock PC error: {e}")
            return {"status": "error", "message": str(e)}


class ShutdownCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "shutdown_system"

    @property
    def requires_confirmation(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return "Initiate Windows shutdown (requires confirmation)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        delay = params.get("value", 0) or 0
        try:
            subprocess.run(f"shutdown /s /t {int(delay)}", shell=True, check=True)
            return {"status": "success", "message": f"System will shut down in {delay} seconds."}
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
            return {"status": "error", "message": str(e)}


class RestartCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "restart_system"

    @property
    def requires_confirmation(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return "Restart the Windows system (requires confirmation)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            subprocess.run("shutdown /r /t 5", shell=True, check=True)
            return {"status": "success", "message": "System will restart in 5 seconds."}
        except Exception as e:
            logger.error(f"Restart error: {e}")
            return {"status": "error", "message": str(e)}


class SleepCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "sleep_system"

    @property
    def description(self) -> str:
        return "Put the system into sleep / hibernate mode."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
            return {"status": "success", "message": "Entering sleep mode."}
        except Exception as e:
            logger.error(f"Sleep error: {e}")
            return {"status": "error", "message": str(e)}


class EmptyRecycleBinCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "empty_recycle_bin"

    @property
    def requires_confirmation(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return "Permanently empty the Windows Recycle Bin (requires confirmation)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import winshell
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            return {"status": "success", "message": "Recycle Bin emptied."}
        except ImportError:
            subprocess.run("rd /s /q %SystemDrive%\\$Recycle.Bin", shell=True)
            return {"status": "success", "message": "Recycle Bin emptied."}
        except Exception as e:
            logger.error(f"Recycle Bin error: {e}")
            return {"status": "error", "message": str(e)}
