"""
System Tray Manager for SARA AI Assistant
Enables minimizing to system tray, background execution, and quick status actions.
"""

import threading
from typing import Callable, Optional
from utils.logger import logger

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False
    logger.warning("pystray or PIL not installed. System tray icon disabled.")


def _create_default_icon():
    """Generate a high-tech cyan HUD circle icon for the system tray."""
    width = 64
    height = 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    # Background cyan circle
    draw.ellipse((4, 4, 60, 60), fill=(10, 14, 26, 255), outline=(0, 229, 255, 255), width=4)
    # Core arc reactor glow
    draw.ellipse((20, 20, 44, 44), fill=(0, 229, 255, 255))
    return image


class SystemTrayManager:
    """Manages the Windows System Tray icon and context menu."""

    def __init__(
        self,
        on_show: Callable[[], None],
        on_exit: Callable[[], None],
        on_trim_memory: Optional[Callable[[], None]] = None
    ):
        self._on_show = on_show
        self._on_exit = on_exit
        self._on_trim_memory = on_trim_memory
        self._icon: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Initialize and run system tray icon in a separate thread."""
        if not HAS_PYSTRAY:
            return

        def _on_show_clicked(icon, item):
            self._on_show()

        def _on_trim_clicked(icon, item):
            if self._on_trim_memory:
                self._on_trim_memory()

        def _on_exit_clicked(icon, item):
            self.stop()
            self._on_exit()

        menu = pystray.Menu(
            pystray.MenuItem("Open SARA HUD", _on_show_clicked, default=True),
            pystray.MenuItem("Trim RAM Memory", _on_trim_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit SARA", _on_exit_clicked)
        )

        icon_image = _create_default_icon()
        self._icon = pystray.Icon("SARA", icon_image, "SARA AI Assistant", menu)

        def _run():
            try:
                self._icon.run()
            except Exception as e:
                logger.error(f"[SystemTray] Tray error: {e}")

        self._thread = threading.Thread(target=_run, name="SARASystemTray", daemon=True)
        self._thread.start()
        logger.info("[SystemTray] System tray icon running.")

    def stop(self) -> None:
        """Stop and remove system tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception as e:
                logger.debug(f"[SystemTray] Stop error: {e}")
            self._icon = None
        logger.info("[SystemTray] System tray icon stopped.")
