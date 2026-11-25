"""
SARA (Smart AI Responsive Assistant) - Main Entry Point
Phase 2: Modern Futuristic GUI (Iron Man JARVIS Theme)
"""

import sys
import os
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
    success = initialize_application()
    if not success:
        sys.exit(1)

    # Launch GUI
    app = SARAMainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
