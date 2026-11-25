"""
Scrollable Chat History Component
Displays structured conversation message bubbles with avatars and timestamps.
"""

import time
import customtkinter as ctk
from gui.theme import Theme

class ChatHistoryView(ctk.CTkScrollableFrame):
    """Scrollable chat history list displaying User and SARA messages."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault('fg_color', Theme.BG_DARK)
        kwargs.setdefault('corner_radius', Theme.CORNER_RADIUS)
        super().__init__(master, **kwargs)
        self._welcome_shown = False
        self.show_welcome_message()

    def show_welcome_message(self):
        """Display initial JARVIS boot greeting."""
        if self._welcome_shown:
            return
        self._welcome_shown = True
        self.add_message(
            sender="SARA",
            text="Hey sir, targeting systems online, ready to serve.",
            is_user=False
        )

    def add_message(self, sender: str, text: str, is_user: bool = False) -> None:
        """Append a new message bubble to the chat stream."""
        timestamp = time.strftime("%H:%M")

        # Message Container Frame (full width row)
        msg_frame = ctk.CTkFrame(self, fg_color="transparent")
        msg_frame.pack(fill="x", padx=Theme.PADDING_MEDIUM, pady=Theme.PADDING_SMALL)

        bubble_bg = Theme.BLUE_ACCENT if is_user else Theme.CARD_BG
        text_color = Theme.TEXT_MAIN
        border_w = 0 if is_user else 1
        border_col = Theme.CYAN_ACCENT if not is_user else Theme.CARD_BG

        # Anchor wrapper to align bubble left or right
        anchor_frame = ctk.CTkFrame(msg_frame, fg_color="transparent")
        anchor_frame.pack(fill="x")

        # Inner Bubble Card
        bubble = ctk.CTkFrame(
            anchor_frame,
            fg_color=bubble_bg,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=border_w,
            border_color=border_col
        )
        if is_user:
            bubble.pack(side="right", padx=(60, 0))
        else:
            bubble.pack(side="left", padx=(0, 60))

        # Header Label (Sender Name + Timestamp)
        header_text = f"YOU  •  {timestamp}" if is_user else f"SARA  •  {timestamp}"
        header_color = Theme.TEXT_MUTED if is_user else Theme.CYAN_ACCENT
        header_lbl = ctk.CTkLabel(
            bubble,
            text=header_text,
            font=Theme.FONT_SMALL,
            text_color=header_color
        )
        header_lbl.pack(anchor="w", padx=Theme.PADDING_MEDIUM, pady=(Theme.PADDING_SMALL, 0))

        # Body Text
        body_lbl = ctk.CTkLabel(
            bubble,
            text=text,
            font=Theme.FONT_BODY,
            text_color=text_color,
            wraplength=460,
            justify="left"
        )
        body_lbl.pack(anchor="w", padx=Theme.PADDING_MEDIUM, pady=(2, Theme.PADDING_SMALL))

        # Auto-scroll to bottom
        self.after(80, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        """Attempt to scroll scrollable frame to the bottom."""
        try:
            self._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass
