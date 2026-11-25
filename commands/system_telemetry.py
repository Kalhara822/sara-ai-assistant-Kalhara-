"""
System Telemetry Commands
Handles: get_cpu_usage, get_ram_usage, get_disk_usage, get_battery_status, get_network_status
"""

import psutil
import socket
from typing import Dict, Any
from commands.base import BaseCommand
from utils.system_info import SystemInfo
from utils.logger import logger


class GetCPUUsageCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_cpu_usage"

    @property
    def description(self) -> str:
        return "Report current CPU utilization percentage."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        cpu = SystemInfo.get_cpu_usage()
        return {"status": "success", "message": f"CPU usage is currently {cpu:.1f} percent.", "value": cpu}


class GetRAMUsageCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_ram_usage"

    @property
    def description(self) -> str:
        return "Report current RAM usage statistics."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        mem = SystemInfo.get_memory_info()
        msg = f"RAM: {mem['used_gb']} GB used out of {mem['total_gb']} GB. ({mem['percent']}% utilization)"
        return {"status": "success", "message": msg, "data": mem}


class GetDiskUsageCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_disk_usage"

    @property
    def description(self) -> str:
        return "Report current disk storage usage."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        disk = SystemInfo.get_disk_info()
        msg = f"Disk: {disk['free_gb']} GB free out of {disk['total_gb']} GB total. ({disk['percent']}% used)"
        return {"status": "success", "message": msg, "data": disk}


class GetBatteryStatusCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_battery_status"

    @property
    def description(self) -> str:
        return "Report laptop battery level and charging status."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        bat = SystemInfo.get_battery_info()
        if not bat.get("available"):
            return {"status": "success", "message": "No battery detected. System is running on AC power."}
        plug = "plugged in and charging" if bat["plugged"] else "on battery power"
        msg = f"Battery is at {bat['percent']:.1f}% and {plug}."
        return {"status": "success", "message": msg, "data": bat}


class GetNetworkStatusCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_network_status"

    @property
    def description(self) -> str:
        return "Check network connectivity status."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return {"status": "success", "message": f"Network is online. Local IP: {ip}.", "ip": ip}
        except OSError:
            return {"status": "success", "message": "Network appears to be offline or disconnected.", "online": False}
