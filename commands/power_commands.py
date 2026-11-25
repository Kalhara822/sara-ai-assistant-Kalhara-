"""
Power Commands
Handles: hibernate, cancel_shutdown, shutdown_after, restart_after,
         check_power_status, check_uptime
All implemented using Windows built-in tools — no extra packages required.
"""

import subprocess
import platform
import datetime
import psutil
from typing import Dict, Any
from commands.base import BaseCommand
from utils.logger import logger


class HibernateCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "hibernate_pc"

    @property
    def description(self) -> str:
        return "Hibernate the PC (saves session to disk and powers off)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            subprocess.run("shutdown /h", shell=True, check=True)
            return {"status": "success", "message": "System is hibernating."}
        except Exception as e:
            logger.error(f"Hibernate error: {e}")
            return {"status": "error", "message": str(e)}


class CancelShutdownCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "cancel_shutdown"

    @property
    def description(self) -> str:
        return "Cancel a pending scheduled shutdown or restart."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = subprocess.run("shutdown /a", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return {"status": "success", "message": "Scheduled shutdown has been cancelled."}
            else:
                return {"status": "info", "message": "No scheduled shutdown was found to cancel."}
        except Exception as e:
            logger.error(f"Cancel shutdown error: {e}")
            return {"status": "error", "message": str(e)}


class ShutdownAfterCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "shutdown_after"

    @property
    def description(self) -> str:
        return "Schedule a shutdown after N minutes."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            minutes = int(params.get("value", 30))
            seconds = minutes * 60
            subprocess.run(f"shutdown /s /t {seconds}", shell=True, check=True)
            return {"status": "success", "message": f"PC will shut down in {minutes} minutes."}
        except Exception as e:
            logger.error(f"Shutdown after error: {e}")
            return {"status": "error", "message": str(e)}


class RestartAfterCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "restart_after"

    @property
    def description(self) -> str:
        return "Schedule a restart after N minutes."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            minutes = int(params.get("value", 5))
            seconds = minutes * 60
            subprocess.run(f"shutdown /r /t {seconds}", shell=True, check=True)
            return {"status": "success", "message": f"PC will restart in {minutes} minutes."}
        except Exception as e:
            logger.error(f"Restart after error: {e}")
            return {"status": "error", "message": str(e)}


class CheckPowerStatusCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "check_power_status"

    @property
    def description(self) -> str:
        return "Report battery level, charging state, and AC power status."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            bat = psutil.sensors_battery()
            if bat is None:
                return {"status": "success", "message": "No battery detected. Running on AC power."}
            pct = bat.percent
            plugged = bat.power_plugged
            secs_left = bat.secsleft
            if plugged:
                status = "plugged in and charging"
            else:
                if secs_left and secs_left != psutil.POWER_TIME_UNLIMITED:
                    hrs = secs_left // 3600
                    mins = (secs_left % 3600) // 60
                    status = f"on battery — about {hrs}h {mins}m remaining"
                else:
                    status = "on battery"
            msg = f"Battery is at {pct:.0f}% and {status}."
            return {"status": "success", "message": msg, "percent": pct, "plugged": plugged}
        except Exception as e:
            logger.error(f"Power status error: {e}")
            return {"status": "error", "message": str(e)}


class CheckUptimeCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "check_uptime"

    @property
    def description(self) -> str:
        return "Report how long the PC has been running since last boot."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            boot_time = psutil.boot_time()
            boot_dt = datetime.datetime.fromtimestamp(boot_time)
            now = datetime.datetime.now()
            delta = now - boot_dt
            hours = int(delta.total_seconds() // 3600)
            minutes = int((delta.total_seconds() % 3600) // 60)
            msg = f"Your PC has been running for {hours} hours and {minutes} minutes since last boot."
            return {"status": "success", "message": msg, "hours": hours, "minutes": minutes}
        except Exception as e:
            logger.error(f"Uptime error: {e}")
            return {"status": "error", "message": str(e)}
