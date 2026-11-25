"""
System Health & Memory Optimization Commands
Handles: trim_memory, get_system_health
"""

from typing import Dict, Any
from commands.base import BaseCommand
from utils.resource_guard import ResourceGuard
from utils.system_info import SystemInfo
from utils.logger import logger

_guard = ResourceGuard()


class TrimMemoryCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "trim_memory"

    @property
    def description(self) -> str:
        return "Trigger Python Garbage Collector and Windows Working Set memory trim."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        result = _guard.trim_memory()
        freed = result.get("freed_mb", 0.0)
        ram_pct = result.get("ram_used_pct", 0.0)
        msg = f"Memory trim complete. Freed approximately {freed:.1f} MB. Current RAM usage is {ram_pct}%."
        logger.info(f"[TrimMemoryCommand] {msg}")
        return {"status": "success", "message": msg, "data": result}


class GetSystemHealthCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_system_health"

    @property
    def description(self) -> str:
        return "Return full system health diagnostics and resource budget status."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        summary = SystemInfo.get_system_summary()
        ram_used = summary["memory"]["percent"]
        cpu_used = summary["cpu_usage_pct"]
        disk_free = summary["disk"]["free_gb"]

        health_status = "Nominal"
        if ram_used > 85 or cpu_used > 90:
            health_status = "Warning (High Load)"

        msg = f"System status: {health_status}. CPU: {cpu_used:.1f}%, RAM: {ram_used}%, Disk Free: {disk_free} GB."
        return {"status": "success", "message": msg, "data": summary}
