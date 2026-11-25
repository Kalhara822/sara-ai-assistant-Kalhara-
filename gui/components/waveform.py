"""
Audio Waveform Visualizer Widget
Renders animated audio frequency bars / sine wave while listening or speaking.
"""

import math
import random
import tkinter as tk
import customtkinter as ctk
from gui.theme import Theme

class WaveformVisualizer(ctk.CTkFrame):
    """Animated audio waveform visualization panel."""

    def __init__(self, master, width: int = 300, height: int = 40, num_bars: int = 24, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.width = width
        self.height = height
        self.num_bars = num_bars

        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            bg=Theme.BG_DARK,
            highlightthickness=0
        )
        self.canvas.pack(expand=True, fill="both")

        self.active = False
        self.status = "ONLINE"
        self.phase = 0.0
        self.levels = [0.1] * self.num_bars
        self._is_animating = True
        self._animate()

    def set_status(self, status: str):
        """Update active status (ONLINE, LISTENING, THINKING, SPEAKING)."""
        self.status = status
        if status in ("LISTENING", "SPEAKING", "THINKING"):
            self.active = True
        else:
            self.active = False

    def set_active(self, active: bool):
        """Enable or disable waveform audio motion."""
        self.active = active

    def set_audio_levels(self, levels: list[float]):
        """Pass live FFT audio amplitude levels."""
        if len(levels) == self.num_bars:
            self.levels = levels

    def _animate(self):
        """Render frame loop."""
        if not self.winfo_exists() or not self._is_animating:
            return

        self.canvas.delete("all")
        self.phase += 0.15

        bar_width = (self.width - 20) / self.num_bars
        mid_y = self.height / 2

        # Select color based on status
        if self.status == "THINKING":
            active_color = "#FF1744"  # Vibrant Red
        elif self.status == "LISTENING":
            active_color = Theme.SUCCESS  # Green
        elif self.status == "SPEAKING":
            active_color = Theme.CYAN_ACCENT  # Cyan
        else:
            active_color = Theme.CYAN_ACCENT

        for i in range(self.num_bars):
            if self.active:
                # Calculate dynamic bar height using sine phase + random jitter
                sine_val = math.sin(self.phase + (i * 0.4))
                amp = (abs(sine_val) * 0.7) + (random.random() * 0.3)
                bar_h = max(4, amp * (self.height - 8))
            else:
                # Flat standby line
                bar_h = 4

            x = 10 + (i * bar_width) + (bar_width / 4)
            y1 = mid_y - (bar_h / 2)
            y2 = mid_y + (bar_h / 2)

            color = active_color if self.active else Theme.TEXT_MUTED
            self.canvas.create_line(
                x, y1, x, y2,
                fill=color,
                width=max(2, int(bar_width / 2))
            )

        self.after(40, self._animate)

    def destroy(self):
        self._is_animating = False
        super().destroy()
