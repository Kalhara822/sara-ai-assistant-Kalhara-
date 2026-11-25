"""
Bottom Typing & Voice Controls Input Bar Component
Entry console supporting both text typing and voice microphone activation.
"""

from typing import Callable, Optional
import customtkinter as ctk
from gui.theme import Theme

class TypingInputArea(ctk.CTkFrame):
    """Input bar with text entry, send button, and mic toggle."""

    def __init__(
        self,
        master,
        on_send_text: Optional[Callable[[str], None]] = None,
        on_toggle_voice: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            height=60,
            **kwargs
        )
        self.pack_propagate(False)

        self.on_send_text = on_send_text
        self.on_toggle_voice = on_toggle_voice
        self.is_listening = False

        # 1. Microphone Toggle Button
        self.mic_btn = ctk.CTkButton(
            self,
            text="🎙 VOICE",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_DARK,
            hover_color=Theme.SUCCESS,
            text_color=Theme.CYAN_ACCENT,
            width=90,
            height=40,
            corner_radius=10,
            command=self._handle_mic_toggle
        )
        self.mic_btn.pack(side="left", padx=Theme.PADDING_MEDIUM)

        # 2. Text Input Entry Box
        self.entry_box = ctk.CTkEntry(
            self,
            placeholder_text="Ask SARA anything or type a command... (e.g. 'Open Chrome')",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_DARK,
            text_color=Theme.TEXT_MAIN,
            placeholder_text_color=Theme.TEXT_MUTED,
            border_color=Theme.CYAN_ACCENT,
            border_width=1,
            height=40,
            corner_radius=10
        )
        self.entry_box.pack(side="left", fill="x", expand=True, padx=(0, Theme.PADDING_MEDIUM))
        self.entry_box.bind("<Return>", lambda event: self._handle_send())

        # 3. Send Button
        self.send_btn = ctk.CTkButton(
            self,
            text="SEND ➤",
            font=Theme.FONT_SUBHEADER,
            fg_color=Theme.CYAN_ACCENT,
            hover_color=Theme.BLUE_ACCENT,
            text_color=Theme.BG_DARK,
            width=90,
            height=40,
            corner_radius=10,
            command=self._handle_send
        )
        self.send_btn.pack(side="right", padx=(0, Theme.PADDING_MEDIUM))

    def _handle_send(self):
        """Submit text typed in entry box."""
        text = self.entry_box.get().strip()
        if text and self.on_send_text:
            self.entry_box.delete(0, "end")
            self.on_send_text(text)

    def _handle_mic_toggle(self):
        """Toggle microphone state."""
        self.is_listening = not self.is_listening
        if self.is_listening:
            self.mic_btn.configure(
                text="🔴 STOP",
                fg_color=Theme.ALERT_DANGER,
                text_color=Theme.TEXT_MAIN
            )
        else:
            self.mic_btn.configure(
                text="🎙 VOICE",
                fg_color=Theme.BG_DARK,
                text_color=Theme.CYAN_ACCENT
            )

        if self.on_toggle_voice:
            self.on_toggle_voice()
