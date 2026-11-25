"""
Display Commands
Handles: get_brightness_level, change_resolution, enable/disable_night_light,
         detect_monitors, switch_display_mode, get_display_info
Uses: screen_brightness_control (already a dependency), Windows built-ins,
      DisplaySwitch.exe, and PowerShell for WMI queries — no new packages.
"""

import subprocess
import re
from typing import Dict, Any
from commands.base import BaseCommand
from utils.logger import logger

try:
    import screen_brightness_control as sbc
    HAS_SBC = True
except Exception:
    HAS_SBC = False


def _run_ps(cmd: str, timeout: int = 8) -> str:
    """Run a PowerShell command and return stdout."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout.strip()


class GetBrightnessLevelCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_brightness_level"

    @property
    def description(self) -> str:
        return "Report the current screen brightness percentage."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if HAS_SBC:
            try:
                level = sbc.get_brightness()
                b = level[0] if isinstance(level, list) else level
                return {"status": "success", "message": f"Screen brightness is at {b}%.", "value": b}
            except Exception as e:
                logger.warning(f"sbc brightness read failed: {e}")
        # Fallback: WMI via PowerShell
        try:
            out = _run_ps(
                "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"
            )
            if out:
                return {"status": "success", "message": f"Screen brightness is at {out}%.", "value": int(out)}
            return {"status": "error", "message": "Could not read brightness on this display."}
        except Exception as e:
            logger.error(f"Get brightness error: {e}")
            return {"status": "error", "message": str(e)}


class ChangeResolutionCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "change_resolution"

    @property
    def description(self) -> str:
        return "Open Display Settings so the user can change screen resolution."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            subprocess.Popen("ms-settings:display", shell=True)
            return {"status": "success", "message": "Opened Display Settings. You can change resolution there."}
        except Exception as e:
            logger.error(f"Change resolution error: {e}")
            return {"status": "error", "message": str(e)}


class EnableNightLightCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "enable_night_light"

    @property
    def description(self) -> str:
        return "Enable Windows Night Light (blue light filter)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Night light via registry toggle + applying it
            ps_cmd = (
                'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\DefaultAccount\\Current\\default$windows.data.bluelightreduction.bluelightreductionstate\\windows.data.bluelightreduction.bluelightreductionstate" '
                '-Name "Data" -Value ([byte[]](0x43,0x42,0x01,0x00,0x0A,0x02,0x01,0x00,0x2A,0x06,0x0A,0x02,0x01,0x00)) -Type Binary -ErrorAction SilentlyContinue'
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=5)
            # Simpler: just open Night Light quick settings
            subprocess.Popen("ms-settings:display", shell=True)
            return {"status": "success", "message": "Night Light settings opened. Toggle Night Light from there, or use the Quick Settings panel."}
        except Exception as e:
            logger.error(f"Night light enable error: {e}")
            return {"status": "error", "message": str(e)}


class DisableNightLightCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "disable_night_light"

    @property
    def description(self) -> str:
        return "Disable Windows Night Light."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            subprocess.Popen("ms-settings:display", shell=True)
            return {"status": "success", "message": "Display Settings opened. Toggle Night Light off from there."}
        except Exception as e:
            logger.error(f"Night light disable error: {e}")
            return {"status": "error", "message": str(e)}


class DetectMonitorsCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "detect_monitors"

    @property
    def description(self) -> str:
        return "Detect and list all connected display monitors."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            out = _run_ps(
                "Get-WmiObject -Namespace root\\wmi -Class WmiMonitorID | "
                "ForEach-Object { ($_.UserFriendlyName | Where-Object {$_ -gt 0} | ForEach-Object {[char]$_}) -join '' }"
            )
            monitors = [m.strip() for m in out.splitlines() if m.strip()]
            count = len(monitors) if monitors else 1
            names = ", ".join(monitors) if monitors else "Primary display"
            return {"status": "success", "message": f"Found {count} monitor(s): {names}.", "monitors": monitors}
        except Exception as e:
            logger.error(f"Detect monitors error: {e}")
            return {"status": "error", "message": str(e)}


class SwitchDisplayModeCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "switch_display_mode"

    @property
    def description(self) -> str:
        return "Switch display mode: extend, duplicate, PC only, or second screen only."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # DisplaySwitch.exe is built into Windows
            query = str(params.get("query", "")).lower()
            if "extend" in query:
                subprocess.Popen("DisplaySwitch.exe /extend", shell=True)
                mode = "Extend"
            elif "duplicate" in query or "mirror" in query or "clone" in query:
                subprocess.Popen("DisplaySwitch.exe /clone", shell=True)
                mode = "Duplicate"
            elif "second" in query or "external" in query:
                subprocess.Popen("DisplaySwitch.exe /external", shell=True)
                mode = "Second screen only"
            else:
                # Default: open the Project panel (Win+P)
                subprocess.Popen("DisplaySwitch.exe /internal", shell=True)
                mode = "PC screen only"
            return {"status": "success", "message": f"Display switched to: {mode}."}
        except Exception as e:
            logger.error(f"Switch display error: {e}")
            return {"status": "error", "message": str(e)}


class GetDisplayInfoCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_display_info"

    @property
    def description(self) -> str:
        return "Show resolution, refresh rate, and display name for connected monitors."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            out = _run_ps(
                "Get-WmiObject -Class Win32_VideoController | "
                "Select-Object Name, CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate | "
                "Format-List"
            )
            if out:
                return {"status": "success", "message": f"Display info:\n{out}"}
            return {"status": "success", "message": "Could not retrieve display details."}
        except Exception as e:
            logger.error(f"Display info error: {e}")
            return {"status": "error", "message": str(e)}
