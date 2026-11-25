"""
HUD Top Header Widget
Displays system status indicator, digital clock, date, and weather info.
"""

import time
import customtkinter as ctk
from gui.theme import Theme

class HeaderWidget(ctk.CTkFrame):
    """Header bar with real-time status and digital clock."""

    def __init__(self, master, on_voice_change=None, **kwargs):
        super().__init__(
            master,
            fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            height=60,
            **kwargs
        )
        self.pack_propagate(False)
        self._on_voice_change = on_voice_change

        # Left Section: Title & Status Indicator
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.pack(side="left", padx=Theme.PADDING_LARGE, fill="y")

        self.title_label = ctk.CTkLabel(
            self.left_frame,
            text="SARA AI",
            font=Theme.FONT_HEADER,
            text_color=Theme.CYAN_ACCENT
        )
        self.title_label.pack(side="left", padx=(0, Theme.PADDING_MEDIUM))

        # Glowing Status Badge
        self.status_badge = ctk.CTkButton(
            self.left_frame,
            text="● ONLINE",
            font=Theme.FONT_STATUS,
            fg_color=Theme.BG_DARK,
            text_color=Theme.CYAN_ACCENT,
            hover=False,
            height=28,
            corner_radius=14
        )
        self.status_badge.pack(side="left")

        # Voice Selector Dropdown
        self.voice_selector = ctk.CTkOptionMenu(
            self.left_frame,
            values=["Voice: Default", "Voice: JARVIS", "Voice: Cute Female"],
            command=self._on_voice_selected,
            width=150,
            height=28,
            fg_color=Theme.BG_DARK,
            button_color=Theme.SURFACE,
            button_hover_color=Theme.ACCENT_BLUE,
            text_color=Theme.CYAN_ACCENT,
            dropdown_fg_color=Theme.CARD_BG,
            dropdown_text_color=Theme.TEXT_MAIN,
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=11, weight="bold")
        )
        self.voice_selector.pack(side="left", padx=(Theme.PADDING_MEDIUM, 0))

        # Center Section: System Notice Banner (replaces chat system logs)
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.pack(side="left", expand=True, fill="both", padx=Theme.PADDING_MEDIUM)

        self.notice_label = ctk.CTkLabel(
            self.center_frame,
            text="",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=10),
            text_color=Theme.ALERT_WARN
        )
        self.notice_label.pack(expand=True)

        # Right Section: Clock & Date
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.pack(side="right", padx=Theme.PADDING_LARGE, fill="y")

        self.clock_label = ctk.CTkLabel(
            self.right_frame,
            text="00:00:00",
            font=Theme.FONT_SUBHEADER,
            text_color=Theme.TEXT_MAIN
        )
        self.clock_label.pack(anchor="e")

        self.date_label = ctk.CTkLabel(
            self.right_frame,
            text="Mon 00 Jan 2026",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        )
        self.date_label.pack(anchor="e")

        self._is_running = True
        self._update_clock()

    def _on_voice_selected(self, choice: str):
        key = "default"
        if "JARVIS" in choice:
            key = "jarvis"
        elif "Cute" in choice:
            key = "cute"
        if self._on_voice_change:
            self._on_voice_change(key)

    def show_system_notice(self, text: str, duration_ms: int = 6000):
        """Display system status notice/warning banner on header bar instead of chat window."""
        self.notice_label.configure(text=f"⚡ {text}")
        self.after(duration_ms, lambda: self.notice_label.configure(text=""))

    def set_status(self, status: str):
        """Update active status badge string and color."""
        if status == "LISTENING":
            self.status_badge.configure(text="● LISTENING", text_color=Theme.SUCCESS)
        elif status == "THINKING":
            self.status_badge.configure(text="● THINKING", text_color="#FF1744")
        elif status == "SPEAKING":
            self.status_badge.configure(text="● SPEAKING", text_color=Theme.CYAN_ACCENT)
        else:
            self.status_badge.configure(text="● ONLINE", text_color=Theme.CYAN_ACCENT)

    def _update_clock(self):
        """Tick digital clock once per second."""
        if not self.winfo_exists() or not self._is_running:
            return

        now = time.strftime("%H:%M:%S")
        date_str = time.strftime("%a, %b %d %Y")

        self.clock_label.configure(text=now)
        self.date_label.configure(text=date_str)

        self.after(1000, self._update_clock)

    def destroy(self):
        self._is_running = False
        super().destroy()
