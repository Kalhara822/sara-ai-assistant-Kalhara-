"""
Quick Actions Bar Component
1-click quick command execution grid for frequent tasks.
"""

from typing import Callable, Optional
import customtkinter as ctk
from gui.theme import Theme

class QuickActionsBar(ctk.CTkFrame):
    """Grid of quick-action command triggers."""

    def __init__(self, master, on_action_clicked: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(
            master,
            fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            **kwargs
        )
        self.on_action_clicked = on_action_clicked

        self.title_lbl = ctk.CTkLabel(
            self,
            text="QUICK ACTIONS",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        )
        self.title_lbl.pack(anchor="w", padx=Theme.PADDING_MEDIUM, pady=(Theme.PADDING_SMALL, 2))

        # Buttons Frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=Theme.PADDING_SMALL, pady=(0, Theme.PADDING_SMALL))

        actions = [
            ("🌐 Chrome", "Open Chrome"),
            ("💻 VS Code", "Open VS Code"),
            ("⚡ Trim RAM", "trim memory"),
            ("📁 Downloads", "organise my downloads"),
            ("📸 Screenshot", "Take a screenshot"),
            ("🔒 Lock PC", "Lock my PC"),
            ("📊 System Health", "get system health"),
        ]

        for icon_label, cmd in actions:
            btn = ctk.CTkButton(
                self.btn_frame,
                text=icon_label,
                font=Theme.FONT_SMALL,
                fg_color=Theme.BG_DARK,
                hover_color=Theme.BLUE_ACCENT,
                text_color=Theme.CYAN_ACCENT,
                height=30,
                corner_radius=8,
                command=lambda c=cmd: self._trigger_action(c)
            )
            btn.pack(side="left", padx=4, expand=True, fill="x")

    def _trigger_action(self, command: str):
        """Invoke callback with action command text."""
        if self.on_action_clicked:
            self.on_action_clicked(command)
