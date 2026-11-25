"""
Plugin Manager Panel — GUI component for SARA's HUD
Shows all loaded plugins with status indicators, actions list, and enable/disable toggle.
Injected as a sidebar panel inside the left control pane.
"""

import customtkinter as ctk
from typing import Callable, List, Dict, Any, Optional
from gui.theme import Theme
from utils.logger import logger


class PluginCard(ctk.CTkFrame):
    """A single plugin info card displayed in the Plugin Manager panel."""

    def __init__(self, parent, plugin_info: Dict[str, Any], **kwargs):
        kwargs.setdefault("fg_color", Theme.SURFACE)
        kwargs.setdefault("corner_radius", 8)
        super().__init__(parent, **kwargs)
        self._plugin_info = plugin_info
        self._enabled = True
        self._build()

    def _build(self):
        name = self._plugin_info.get("name", "Unknown")
        version = self._plugin_info.get("version", "?")
        actions = self._plugin_info.get("actions", [])
        status = self._plugin_info.get("status", "loaded")

        # Status dot color
        status_color = Theme.ACCENT_GREEN if status == "loaded" else Theme.ACCENT_WARN

        # Top row: name + version + status dot
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            top_row,
            text="●",
            text_color=status_color,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            top_row,
            text=name.replace("Plugin", "").replace("_", " ").strip(),
            font=ctk.CTkFont(family=Theme.FONT_PRIMARY, size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text=f"v{version}",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=10),
            text_color=Theme.TEXT_MUTED,
        ).pack(side="right")

        # Actions list
        if actions:
            actions_text = " · ".join(a.replace("_", " ") for a in actions[:4])
            ctk.CTkLabel(
                self,
                text=actions_text,
                font=ctk.CTkFont(family=Theme.FONT_MONO, size=9),
                text_color=Theme.ACCENT_CYAN,
                wraplength=220,
                anchor="w",
                justify="left",
            ).pack(fill="x", padx=12, pady=(0, 8))


class PluginManagerPanel(ctk.CTkFrame):
    """
    Plugin Manager Panel — embedded into SARA's control HUD.
    Lists all registered plugins with live status, count, and action tags.
    """

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("fg_color", Theme.CARD_BG)
        kwargs.setdefault("corner_radius", Theme.CORNER_RADIUS)
        super().__init__(parent, **kwargs)
        self._cards: List[PluginCard] = []
        self._build()

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            header,
            text="[ PLUGIN MODULES ]",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=11, weight="bold"),
            text_color=Theme.ACCENT_CYAN,
        ).pack(side="left")

        self._count_label = ctk.CTkLabel(
            header,
            text="0 loaded",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=10),
            text_color=Theme.TEXT_MUTED,
        )
        self._count_label.pack(side="right")

        # Divider line
        ctk.CTkFrame(self, fg_color=Theme.ACCENT_CYAN, height=1).pack(fill="x", padx=12, pady=(0, 6))

        # Scrollable plugin list
        self._scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Theme.ACCENT_CYAN,
            scrollbar_button_hover_color=Theme.ACCENT_BLUE,
        )
        self._scroll_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Empty state label
        self._empty_label = ctk.CTkLabel(
            self._scroll_frame,
            text="No plugins loaded yet...",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=10),
            text_color=Theme.TEXT_MUTED,
        )
        self._empty_label.pack(pady=20)

    def refresh(self, plugins: List[Dict[str, Any]]):
        """
        Refresh the panel with a fresh list of plugin info dicts.
        Called by SARAEngine after plugin discovery completes.
        """
        # Clear existing cards
        for card in self._cards:
            card.destroy()
        self._cards.clear()

        if plugins:
            self._empty_label.pack_forget()
            for info in plugins:
                card = PluginCard(self._scroll_frame, info)
                card.pack(fill="x", pady=3, padx=2)
                self._cards.append(card)
        else:
            self._empty_label.pack(pady=20)

        self._count_label.configure(
            text=f"{len(plugins)} loaded",
            text_color=Theme.ACCENT_GREEN if plugins else Theme.TEXT_MUTED
        )

        logger.debug(f"PluginManagerPanel refreshed — {len(plugins)} plugins.")

    def show_error(self, plugin_name: str, error: str):
        """Append a failed plugin card with error styling."""
        info = {"name": plugin_name, "version": "?", "actions": [], "status": "error"}
        card = PluginCard(self._scroll_frame, info)
        card.pack(fill="x", pady=3, padx=2)
        self._cards.append(card)
