"""
System Monitor Commands (Extended)
Handles: show_running_apps, kill_process, get_cpu_temperature,
         get_laptop_specs, get_windows_version, get_available_storage,
         clear_temp_files, record_screen, stop_recording, start_screen_sharing
All use psutil + PowerShell WMI + stdlib — no heavy packages.
"""

import os
import re
import shutil
import subprocess
import platform
import datetime
from typing import Dict, Any
from commands.base import BaseCommand
from utils.logger import logger

import psutil

_recording_process = None  # Global for screen recording state


def _run_ps(cmd: str, timeout: int = 10) -> str:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout.strip()


class ShowRunningAppsCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "show_running_apps"

    @property
    def description(self) -> str:
        return "List the currently running applications (top CPU consumers)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            procs = []
            for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
                try:
                    info = p.info
                    if info['cpu_percent'] is not None:
                        procs.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            # Sort by CPU, take top 10
            procs.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            top = procs[:10]
            lines = [f"{p['name']} (CPU: {p['cpu_percent']:.1f}%, RAM: {p['memory_percent']:.1f}%)" for p in top]
            msg = "Top running apps:\n" + "\n".join(lines)
            return {"status": "success", "message": msg, "processes": lines}
        except Exception as e:
            logger.error(f"Show running apps error: {e}")
            return {"status": "error", "message": str(e)}


class KillProcessCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "kill_process"

    @property
    def requires_confirmation(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return "Terminate a running process by name."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            name = (params.get("query") or params.get("application") or "").strip().lower()
            if not name:
                return {"status": "error", "message": "Please specify a process name to kill. E.g. 'kill notepad'"}
            killed = []
            for p in psutil.process_iter(['name', 'pid']):
                try:
                    if name in p.info['name'].lower():
                        p.terminate()
                        killed.append(p.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if killed:
                return {"status": "success", "message": f"Terminated: {', '.join(set(killed))}."}
            return {"status": "info", "message": f"No running process found matching '{name}'."}
        except Exception as e:
            logger.error(f"Kill process error: {e}")
            return {"status": "error", "message": str(e)}


class GetCPUTemperatureCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_cpu_temperature"

    @property
    def description(self) -> str:
        return "Report the current CPU temperature."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Try psutil sensors
            temps = psutil.sensors_temperatures() if hasattr(psutil, 'sensors_temperatures') else {}
            if temps:
                for key in ['coretemp', 'k10temp', 'cpu_thermal']:
                    if key in temps:
                        avg = sum(t.current for t in temps[key]) / len(temps[key])
                        return {"status": "success", "message": f"CPU temperature is {avg:.1f}°C.", "celsius": avg}
            # Fallback: WMI via PowerShell
            out = _run_ps(
                "(Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace 'root/wmi').CurrentTemperature"
            )
            if out:
                lines = [l.strip() for l in out.splitlines() if l.strip().isdigit()]
                if lines:
                    kelvin = int(lines[0]) / 10.0
                    celsius = kelvin - 273.15
                    return {"status": "success", "message": f"CPU temperature is approximately {celsius:.1f}°C.", "celsius": celsius}
            return {"status": "info", "message": "Temperature sensors not accessible on this system. This is normal on some laptops."}
        except Exception as e:
            logger.error(f"CPU temperature error: {e}")
            return {"status": "info", "message": "Could not read CPU temperature from this system."}


class GetLaptopSpecsCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_laptop_specs"

    @property
    def description(self) -> str:
        return "Show detailed hardware specifications of this laptop."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            cpu = platform.processor() or "Unknown CPU"
            cores = psutil.cpu_count(logical=False)
            threads = psutil.cpu_count(logical=True)
            ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
            disks = psutil.disk_partitions()
            disk_info = []
            for d in disks:
                try:
                    usage = psutil.disk_usage(d.mountpoint)
                    disk_info.append(f"{d.device} ({round(usage.total/(1024**3),1)} GB)")
                except Exception:
                    pass
            win_ver = platform.version()
            win_release = platform.release()

            # GPU via PowerShell
            gpu = _run_ps("(Get-WmiObject Win32_VideoController).Name")

            msg = (
                f"Laptop Specs:\n"
                f"  CPU: {cpu} ({cores} cores, {threads} threads)\n"
                f"  RAM: {ram_gb} GB\n"
                f"  GPU: {gpu or 'N/A'}\n"
                f"  Disks: {', '.join(disk_info)}\n"
                f"  OS: Windows {win_release} (Build {win_ver})"
            )
            return {"status": "success", "message": msg}
        except Exception as e:
            logger.error(f"Laptop specs error: {e}")
            return {"status": "error", "message": str(e)}


class GetWindowsVersionCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_windows_version"

    @property
    def description(self) -> str:
        return "Show the current Windows version and build number."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            release = platform.release()
            version = platform.version()
            # Get friendly name (e.g. "Windows 11 Home")
            edition = _run_ps("(Get-WmiObject Win32_OperatingSystem).Caption")
            if not edition:
                edition = f"Windows {release}"
            return {"status": "success", "message": f"{edition} (Build {version})."}
        except Exception as e:
            logger.error(f"Windows version error: {e}")
            return {"status": "error", "message": str(e)}


class GetAvailableStorageCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_available_storage"

    @property
    def description(self) -> str:
        return "Show free and total disk space on all drives."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            lines = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    free = round(usage.free / (1024**3), 1)
                    total = round(usage.total / (1024**3), 1)
                    pct_used = usage.percent
                    lines.append(f"  {part.device}: {free} GB free of {total} GB ({pct_used}% used)")
                except Exception:
                    pass
            msg = "Storage:\n" + "\n".join(lines)
            return {"status": "success", "message": msg}
        except Exception as e:
            logger.error(f"Available storage error: {e}")
            return {"status": "error", "message": str(e)}


class ClearTempFilesCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "clear_temp_files"

    @property
    def description(self) -> str:
        return "Delete temporary files from the Windows Temp and user Temp folders."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            temp_paths = [
                os.environ.get("TEMP", ""),
                os.environ.get("TMP", ""),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Temp"),
            ]
            deleted = 0
            failed = 0
            for temp_dir in temp_paths:
                if not temp_dir or not os.path.isdir(temp_dir):
                    continue
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                            deleted += 1
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                            deleted += 1
                    except Exception:
                        failed += 1
            msg = f"Cleaned temporary files: {deleted} items removed, {failed} skipped (in use)."
            logger.info(msg)
            return {"status": "success", "message": msg}
        except Exception as e:
            logger.error(f"Clear temp error: {e}")
            return {"status": "error", "message": str(e)}


class RecordScreenCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "record_screen"

    @property
    def description(self) -> str:
        return "Start screen recording using Windows built-in Xbox Game Bar (Win+Alt+R)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Use Windows Game Bar shortcut — built-in, zero extra packages
            import ctypes
            # Simulate Win+Alt+R via PowerShell SendKeys
            ps_cmd = (
                '$wsh = New-Object -ComObject WScript.Shell; '
                '$wsh.SendKeys("^%{r}")'  # This won't work perfectly but tries
            )
            # Better: open Game Bar directly
            subprocess.Popen("start ms-gamebar:", shell=True)
            return {
                "status": "success",
                "message": (
                    "Xbox Game Bar opened. Press Win+Alt+R to start/stop recording. "
                    "Recordings are saved in your Videos\\Captures folder."
                )
            }
        except Exception as e:
            logger.error(f"Record screen error: {e}")
            return {"status": "error", "message": str(e)}


class StopRecordingCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "stop_recording"

    @property
    def description(self) -> str:
        return "Stop screen recording (Xbox Game Bar)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            subprocess.Popen("start ms-gamebar:", shell=True)
            return {"status": "success", "message": "Press Win+Alt+R to stop recording. Check Videos\\Captures for the file."}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class StartScreenSharingCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "start_screen_sharing"

    @property
    def description(self) -> str:
        return "Open Windows Quick Assist for screen sharing."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            subprocess.Popen("quickassist", shell=True)
            return {"status": "success", "message": "Opened Quick Assist for screen sharing."}
        except Exception as e:
            logger.error(f"Screen sharing error: {e}")
            try:
                subprocess.Popen("ms-settings:project", shell=True)
                return {"status": "success", "message": "Opened screen projection settings."}
            except Exception:
                return {"status": "error", "message": str(e)}
