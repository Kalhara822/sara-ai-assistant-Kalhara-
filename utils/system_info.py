"""
Hardware & Telemetry Diagnostics for SARA AI Assistant
Targeted for Dell Inspiron 3511 / Intel Core i3 11th Gen / Windows 11
"""

import os
import sys
import platform
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from typing import Dict, Any
from utils.logger import logger

class SystemInfo:
    """Utility class to collect hardware and OS metrics."""

    @staticmethod
    def get_cpu_usage() -> float:
        """Returns current CPU utilization percentage."""
        if not HAS_PSUTIL:
            return 0.0
        return psutil.cpu_percent(interval=None)

    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Returns RAM usage statistics in GB and percentage."""
        if not HAS_PSUTIL:
            return {"total_gb": 12.0, "available_gb": 6.0, "used_gb": 6.0, "percent": 50.0}
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "percent": mem.percent
        }

    @staticmethod
    def get_disk_info() -> Dict[str, Any]:
        """Returns primary disk usage metrics."""
        if not HAS_PSUTIL:
            return {"total_gb": 256.0, "free_gb": 128.0, "used_gb": 128.0, "percent": 50.0}
        disk = psutil.disk_usage('/')
        return {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "percent": disk.percent
        }

    @staticmethod
    def get_battery_info() -> Dict[str, Any]:
        """Returns laptop battery status if available."""
        if not HAS_PSUTIL:
            return {"available": False, "percent": 100, "plugged": True}
        battery = psutil.sensors_battery()
        if battery is None:
            return {"available": False, "percent": 100, "plugged": True}
        return {
            "available": True,
            "percent": battery.percent,
            "plugged": battery.power_plugged,
            "seconds_left": battery.secsleft
        }

    @staticmethod
    def get_system_summary() -> Dict[str, Any]:
        """Returns full diagnostic snapshot."""
        return {
            "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            "processor": platform.processor(),
            "cpu_count_logical": psutil.cpu_count(logical=True) if HAS_PSUTIL else os.cpu_count() or 4,
            "cpu_count_physical": psutil.cpu_count(logical=False) if HAS_PSUTIL else 2,
            "cpu_usage_pct": SystemInfo.get_cpu_usage(),
            "memory": SystemInfo.get_memory_info(),
            "disk": SystemInfo.get_disk_info(),
            "battery": SystemInfo.get_battery_info()
        }

    @staticmethod
    def log_diagnostics() -> None:
        """Logs initial hardware diagnostic startup report."""
        diag = SystemInfo.get_system_summary()
        logger.info("=== SARA HARDWARE DIAGNOSTICS ===")
        logger.info(f"OS: {diag['os']}")
        logger.info(f"Processor: {diag['processor']}")
        logger.info(f"CPU Cores: {diag['cpu_count_physical']} physical, {diag['cpu_count_logical']} logical")
        logger.info(f"RAM Total: {diag['memory']['total_gb']} GB (Used: {diag['memory']['percent']}%)")
        logger.info(f"Disk Free: {diag['disk']['free_gb']} GB / {diag['disk']['total_gb']} GB")
        logger.info("=================================")
