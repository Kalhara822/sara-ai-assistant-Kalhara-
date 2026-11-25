
import math
import tkinter as tk
import customtkinter as ctk
from gui.theme import Theme

class IronManArcReactor(ctk.CTkFrame):
    """Large animated Iron Man-style Arc Reactor for SARA."""

    def __init__(self, master, size: int = 280, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.size = size
        self.canvas_size = size + 30
        self.center = self.canvas_size / 2

        self.canvas = tk.Canvas(
            self,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=Theme.BG_DARK,
            highlightthickness=0
        )
        self.canvas.pack(expand=True, fill="both")

        self.angle = 0.0
        self.inner_angle = 0.0
        self.pulse = 0.0
        self.pulse_dir = 1

        self.status = "ONLINE"
        self.active = False
        self._is_animating = True

        self._animate()

    def set_status(self, status: str):
        self.status = status.upper()

        # Blue when idle, red whenever a conversation is active.
        self.active = self.status in {
            "LISTENING",
            "THINKING",
            "SPEAKING",
            "CONVERSATION",
            "ACTIVE"
        }

    def set_conversation_active(self, active: bool):
        self.active = bool(active)
        self.status = "ACTIVE" if active else "ONLINE"

    def _animate(self):
        if not self.winfo_exists() or not self._is_animating:
            return

        self.canvas.delete("all")

        # Color and animation speed
        if self.active:
            core_color = "#FF2525"
            glow_color = "#FF5555"
            outer_color = "#8B1010"
            speed = 0.105
            pulse_speed = 0.055
        else:
            core_color = "#00CFFF"
            glow_color = "#38BFFF"
            outer_color = "#075C9C"
            speed = 0.035
            pulse_speed = 0.025

        self.angle += speed
        self.inner_angle -= speed * 0.55

        self.pulse += pulse_speed * self.pulse_dir

        if self.pulse >= 1.0 or self.pulse <= 0.0:
            self.pulse_dir *= -1

        cx = self.center
        cy = self.center

        # Reactor dimensions
        r_outer = self.size * 0.46
        r_ring = self.size * 0.37
        r_middle = self.size * 0.28
        r_core = self.size * 0.19

        # 1. Outer energy glow rings
        for i in range(3):
            radius = r_outer + i * 4
            self.canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                outline=outer_color,
                width=1
            )

        # 2. Main outer rotating segmented ring
        for i in range(24):
            theta = self.angle + i * (math.tau / 24)

            start = math.degrees(theta)
            self.canvas.create_arc(
                cx - r_ring, cy - r_ring,
                cx + r_ring, cy + r_ring,
                start=start,
                extent=9,
                style="arc",
                outline=core_color,
                width=4
            )

        # 3. Rotating mechanical spokes
        for i in range(12):
            theta = self.inner_angle + i * (math.tau / 12)

            x1 = cx + r_middle * math.cos(theta)
            y1 = cy + r_middle * math.sin(theta)

            x2 = cx + (r_middle - 17) * math.cos(theta)
            y2 = cy + (r_middle - 17) * math.sin(theta)

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=glow_color,
                width=4
            )

        # 4. Middle energy ring
        mid_pulse = self.pulse * 5

        self.canvas.create_oval(
            cx - r_middle - mid_pulse,
            cy - r_middle - mid_pulse,
            cx + r_middle + mid_pulse,
            cy + r_middle + mid_pulse,
            outline=glow_color,
            width=2
        )

        # 5. Inner rotating triangle
        triangle_radius = r_core * 0.85
        points = []

        for i in range(3):
            theta = self.angle * 0.5 + i * (math.tau / 3)

            points.extend([
                cx + triangle_radius * math.cos(theta),
                cy + triangle_radius * math.sin(theta)
            ])

        self.canvas.create_polygon(
            points,
            fill="",
            outline=core_color,
            width=4
        )

        # 6. Central reactor housing
        self.canvas.create_oval(
            cx - r_core, cy - r_core,
            cx + r_core, cy + r_core,
            fill="#101C2A",
            outline=core_color,
            width=4
        )

        # 7. Central energy core
        core_radius = 15 + self.pulse * 7

        self.canvas.create_oval(
            cx - core_radius,
            cy - core_radius,
            cx + core_radius,
            cy + core_radius,
            fill=core_color,
            outline="#FFFFFF",
            width=2
        )

        # 8. Six outer energy nodes
        for i in range(6):
            theta = self.angle + i * (math.tau / 6)

            nx = cx + (r_middle + 12) * math.cos(theta)
            ny = cy + (r_middle + 12) * math.sin(theta)

            node_radius = 4 + self.pulse * 2

            self.canvas.create_oval(
                nx - node_radius,
                ny - node_radius,
                nx + node_radius,
                ny + node_radius,
                fill=glow_color,
                outline=""
            )

        # 9. Reactor status
        status_text = "CONVERSATION ACTIVE" if self.active else "SARA ONLINE"

        self.canvas.create_text(
            cx,
            cy + r_outer + 17,
            text=status_text,
            fill=core_color,
            font=("Consolas", 10, "bold")
        )

        self.after(33, self._animate)

    def destroy(self):
        self._is_animating = False
        super().destroy()

class AnimatedAICore(ctk.CTkFrame):
    """Single large animated Arc Reactor HUD."""

    def __init__(self, master, size: int = 280, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.arc_reactor = IronManArcReactor(
            self,
            size=size
        )

        self.arc_reactor.pack(
            expand=True,
            fill="both",
            padx=5,
            pady=5
        )

    def set_status(self, status: str):
        self.arc_reactor.set_status(status)

    def set_conversation_active(self, active: bool):
        self.arc_reactor.set_conversation_active(active)