"""
SARA (Smart AI Responsive Assistant) - Main Entry Point
Phase 2: Modern Futuristic GUI (Iron Man JARVIS Theme)
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import config
from utils.logger import logger
from utils.system_info import SystemInfo
from plugins.base import PluginManager
from gui.main_window import SARAMainWindow


def _ensure_ollama_running() -> None:
    """Check if Ollama is reachable; if not, auto-start it in the background."""
    try:
        import ollama as _ol
        _ol.list()           # quick ping — raises ConnectionError if down
        logger.info("Ollama AI daemon is already running.")
        return
    except Exception:
        pass

    logger.info("Ollama not detected — attempting to start 'ollama serve' in background...")
    try:
        # Launch ollama serve as a hidden background process (no console window)
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        subprocess.Popen(
            ["ollama", "serve"],
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Give it a few seconds to warm up
        for attempt in range(1, 7):
            time.sleep(2)
            try:
                import ollama as _ol
                _ol.list()
                logger.info(f"Ollama started successfully (attempt {attempt}).")
                return
            except Exception:
                logger.debug(f"Waiting for Ollama... ({attempt}/6)")

        logger.warning("Ollama did not respond after 12 seconds. AI chat will be limited.")
    except FileNotFoundError:
        logger.warning("'ollama' executable not found in PATH. AI chat will be limited. Download from https://ollama.com")

def initialize_application() -> bool:
    """Initialize system directories, logging, and environment checks."""
    try:
        logger.info("==================================================")
        logger.info("Initializing SARA (Smart AI Responsive Assistant)")
        logger.info("Target: Windows 11 | Hardware: Intel i3 / 12GB RAM")
        logger.info("==================================================")

        # Ensure runtime folders exist
        config.ensure_directories()
        logger.info("Runtime directories verified.")

        # Log system telemetry
        SystemInfo.log_diagnostics()

        # Initialize Plugin Registry
        plugin_manager = PluginManager()
        logger.info("Plugin Manager initialized.")

        logger.info("Initialization completed successfully. Launching GUI...")
        return True
    except Exception as e:
        logger.critical(f"Failed to initialize SARA application: {e}", exc_info=True)
        return False

def main():
    """Application main entry point."""
    # Auto-start Ollama AI daemon if not already running
    _ensure_ollama_running()

    success = initialize_application()
    if not success:
        sys.exit(1)

    # Launch GUI
    app = SARAMainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
