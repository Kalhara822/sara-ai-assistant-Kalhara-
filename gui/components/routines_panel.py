"""
Routines Panel — GUI component for SARA's HUD
Displays all available smart routines with one-click execution buttons.
Shows run count, step count, and live status per routine.
"""

import customtkinter as ctk
from typing import Callable, List, Dict, Any
from gui.theme import Theme
from utils.logger import logger

# Routine → icon emoji mapping
ROUTINE_ICONS = {
    "morning":       "☀️",
    "work":          "💼",
    "night":         "🌙",
    "dev setup":     "⚡",
    "presentation":  "📊",
    "lock and go":   "🔒",
    "focus":         "🎯",
}


class RoutineCard(ctk.CTkFrame):
    """Single clickable routine card with name, description, steps count, and run button."""

    def __init__(self, parent, routine: Dict[str, Any], on_run: Callable[[str], None], **kwargs):
        kwargs.setdefault("fg_color", Theme.SURFACE)
        kwargs.setdefault("corner_radius", 8)
        super().__init__(parent, **kwargs)
        self._routine = routine
        self._on_run = on_run
        self._running = False
        self._build()

    def _build(self):
        name = self._routine.get("name", "?")
        desc = self._routine.get("description", "")
        steps = self._routine.get("steps", 0)
        is_builtin = self._routine.get("is_builtin", False)
        icon = ROUTINE_ICONS.get(name, "🔧")

        # Outer padding frame
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=6)
        inner.columnconfigure(1, weight=1)

        # Icon label
        ctk.CTkLabel(
            inner,
            text=icon,
            font=ctk.CTkFont(size=18),
            width=28,
        ).grid(row=0, column=0, rowspan=2, padx=(0, 8), sticky="w")

        # Name + badge
        name_row = ctk.CTkFrame(inner, fg_color="transparent")
        name_row.grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(
            name_row,
            text=name.title(),
            font=ctk.CTkFont(family=Theme.FONT_PRIMARY, size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        if is_builtin:
            ctk.CTkLabel(
                name_row,
                text=" BUILT-IN",
                font=ctk.CTkFont(family=Theme.FONT_MONO, size=8),
                text_color=Theme.ACCENT_CYAN,
            ).pack(side="left", padx=4)

        ctk.CTkLabel(
            name_row,
            text=f"{steps} steps",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=9),
            text_color=Theme.TEXT_MUTED,
        ).pack(side="right")

        # Description
        if desc:
            ctk.CTkLabel(
                inner,
                text=desc,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=9),
                text_color=Theme.TEXT_MUTED,
                anchor="w",
                wraplength=190,
                justify="left",
            ).grid(row=1, column=1, sticky="ew")

        # Run button
        self._run_btn = ctk.CTkButton(
            self,
            text="▶  RUN",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=10, weight="bold"),
            fg_color=Theme.ACCENT_CYAN,
            text_color=Theme.BG_DARK,
            hover_color=Theme.ACCENT_BLUE,
            height=26,
            corner_radius=6,
            command=self._handle_run,
        )
        self._run_btn.pack(fill="x", padx=8, pady=(0, 8))

    def _handle_run(self):
        """Flash button state and fire callback."""
        if self._running:
            return
        self._running = True
        self._run_btn.configure(text="⏳  RUNNING...", fg_color=Theme.ACCENT_WARN, state="disabled")
        self._on_run(self._routine["name"])
        # Reset button after 3 seconds
        self.after(3000, self._reset_btn)

    def _reset_btn(self):
        self._running = False
        self._run_btn.configure(text="▶  RUN", fg_color=Theme.ACCENT_GREEN, state="normal")
        # Fade back to cyan
        self.after(2000, lambda: self._run_btn.configure(fg_color=Theme.ACCENT_CYAN))


class RoutinesPanel(ctk.CTkFrame):
    """
    Routines Panel — embedded into SARA's right sidebar or a modal overlay.
    Lists all available routines with live run controls.
    """

    def __init__(self, parent, on_run_routine: Callable[[str], None], **kwargs):
        kwargs.setdefault("fg_color", Theme.CARD_BG)
        kwargs.setdefault("corner_radius", Theme.CORNER_RADIUS)
        super().__init__(parent, **kwargs)
        self._on_run = on_run_routine
        self._cards: List[RoutineCard] = []
        self._build()

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            header,
            text="[ SMART ROUTINES ]",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=11, weight="bold"),
            text_color=Theme.ACCENT_CYAN,
        ).pack(side="left")

        self._count_label = ctk.CTkLabel(
            header,
            text="0 routines",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=10),
            text_color=Theme.TEXT_MUTED,
        )
        self._count_label.pack(side="right")

        # Divider
        ctk.CTkFrame(self, fg_color=Theme.ACCENT_CYAN, height=1).pack(fill="x", padx=12, pady=(0, 6))

        # Scrollable list
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Theme.ACCENT_CYAN,
            scrollbar_button_hover_color=Theme.ACCENT_BLUE,
        )
        self._scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="Loading routines...",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=10),
            text_color=Theme.TEXT_MUTED,
        )
        self._empty_label.pack(pady=20)

    def refresh(self, routines: List[Dict[str, Any]]) -> None:
        """Populate panel with routine cards."""
        for card in self._cards:
            card.destroy()
        self._cards.clear()

        if routines:
            self._empty_label.pack_forget()
            for r in routines:
                card = RoutineCard(self._scroll, r, on_run=self._on_run)
                card.pack(fill="x", pady=3, padx=2)
                self._cards.append(card)
        else:
            self._empty_label.configure(text="No routines available.")
            self._empty_label.pack(pady=20)

        self._count_label.configure(
            text=f"{len(routines)} routine{'s' if len(routines) != 1 else ''}",
            text_color=Theme.ACCENT_GREEN if routines else Theme.TEXT_MUTED,
        )
        logger.debug(f"RoutinesPanel refreshed — {len(routines)} routines.")
