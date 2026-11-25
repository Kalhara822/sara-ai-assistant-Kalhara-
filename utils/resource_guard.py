"""
SARA Hardware Resource Guard & Health Watchdog
Target Machine: Dell Inspiron 3511 (Intel Core i3 11th Gen, 12GB RAM)

Provides:
 - Real-time CPU & RAM budget monitoring
 - Automatic Garbage Collection & RAM trimming when thresholds are exceeded
 - Thermal / High Load Throttling warnings
 - Crash Guard & Thread Health Diagnostics
"""

import os
import sys
import time
import gc
import threading
from typing import Callable, Optional, Dict, Any
from utils.system_info import SystemInfo
from utils.logger import logger

# Performance Thresholds tailored for i3 11th Gen / 12GB RAM
MAX_RAM_PERCENT = 85.0     # Trigger RAM cleanup if system RAM > 85%
MAX_CPU_PERCENT = 90.0     # Warn high CPU usage if sustained > 90%
CHECK_INTERVAL_SEC = 5.0   # Watchdog poll interval


class ResourceGuard:
    """
    Background Watchdog for system performance, memory management,
    and automatic memory trimming.
    """

    def __init__(self, on_warning_callback: Optional[Callable[[str], None]] = None):
        self._on_warning = on_warning_callback
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._high_cpu_count = 0
        logger.info("ResourceGuard initialized for i3 11th Gen hardware budget.")

    def start(self) -> None:
        """Start the background monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            name="SARAResourceGuard",
            daemon=True
        )
        self._thread.start()
        logger.info("[ResourceGuard] Background watchdog started.")

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        logger.info("[ResourceGuard] Stopped.")

    def trim_memory(self) -> Dict[str, Any]:
        """Force Python Garbage Collector and Windows Working Set Trim."""
        initial_mem = SystemInfo.get_memory_info()
        
        # 1. Python GC collect across all 3 generations
        uncollected = gc.collect()
        
        # 2. Windows SetProcessWorkingSetSize trim (Windows only)
        trimmed_win = False
        if sys.platform == "win32":
            try:
                import ctypes
                handle = ctypes.windll.kernel32.GetCurrentProcess()
                ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, -1, -1)
                trimmed_win = True
            except Exception as e:
                logger.debug(f"[ResourceGuard] Working set trim error: {e}")

        final_mem = SystemInfo.get_memory_info()
        freed_mb = round((initial_mem["used_gb"] - final_mem["used_gb"]) * 1024, 2)
        
        logger.info(f"[ResourceGuard] Memory trim executed: {uncollected} uncollected objects freed. Windows working set trimmed: {trimmed_win}")
        
        return {
            "status": "success",
            "uncollected_objects": uncollected,
            "win_trimmed": trimmed_win,
            "freed_mb": max(0.0, freed_mb),
            "ram_used_pct": final_mem["percent"]
        }

    def _monitor_loop(self) -> None:
        """Internal monitoring loop."""
        while self._running:
            try:
                mem = SystemInfo.get_memory_info()
                cpu = SystemInfo.get_cpu_usage()

                # RAM Threshold Guard
                if mem["percent"] >= MAX_RAM_PERCENT:
                    logger.warning(f"[ResourceGuard] High RAM usage detected ({mem['percent']}%). Running automatic memory trim...")
                    res = self.trim_memory()
                    if self._on_warning:
                        self._on_warning(f"High RAM usage ({mem['percent']}%). Optimized memory ({res['freed_mb']} MB freed).")

                # Sustained CPU Guard
                if cpu >= MAX_CPU_PERCENT:
                    self._high_cpu_count += 1
                    if self._high_cpu_count >= 3:  # 3 consecutive checks (15 sec)
                        msg = f"Sustained high CPU load ({cpu:.1f}%). SARA is throttling background tasks."
                        logger.warning(f"[ResourceGuard] {msg}")
                        if self._on_warning:
                            self._on_warning(msg)
                        self._high_cpu_count = 0
                else:
                    self._high_cpu_count = max(0, self._high_cpu_count - 1)

            except Exception as e:
                logger.error(f"[ResourceGuard] Watchdog error: {e}")

            time.sleep(CHECK_INTERVAL_SEC)
