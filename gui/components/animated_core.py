"""
Dual HUD Visualizer: Iron Man Arc Reactor + Pygame-Inspired Cyber AI Girl Face
Displays Iron Man's classic glowing Arc Reactor alongside the animated Cyber AI Girl Avatar Face.
"""

import math
import random
import time
import tkinter as tk
import customtkinter as ctk
from gui.theme import Theme
from gui.components.avatar_controller import AIAvatarAnimationController


class IronManArcReactor(ctk.CTkFrame):
    """Classic Iron Man Arc Reactor circular core with rotating spokes and pulse effects."""

    def __init__(self, master, size: int = 140, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.size = size
        self.canvas_size = size + 16
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
        self.pulse = 0.0
        self.pulse_dir = 1
        self.status = "ONLINE"
        self._is_animating = True
        self._animate()

    def set_status(self, status: str):
        self.status = status

    def _animate(self):
        if not self.winfo_exists() or not self._is_animating:
            return

        self.canvas.delete("all")

        if self.status == "LISTENING":
            core_color = Theme.SUCCESS
            speed = 0.08
        elif self.status == "THINKING":
            core_color = Theme.ALERT_WARN
            speed = 0.12
        elif self.status == "SPEAKING":
            core_color = Theme.CYAN_ACCENT
            speed = 0.10
        else:
            core_color = Theme.CYAN_ACCENT
            speed = 0.04

        self.angle += speed
        self.pulse += 0.03 * self.pulse_dir
        if self.pulse >= 1.0 or self.pulse <= 0.0:
            self.pulse_dir *= -1

        r_outer = (self.size / 2) - 4
        r_inner = (self.size / 2) - 16
        r_core = (self.size / 2) - 30

        # 1. Outer Glow Ring
        self.canvas.create_oval(
            self.center - r_outer, self.center - r_outer,
            self.center + r_outer, self.center + r_outer,
            outline=Theme.BLUE_ACCENT, width=2
        )

        # 2. Pulsing Mid Arc Ring
        pulse_r = r_inner + (self.pulse * 3)
        self.canvas.create_oval(
            self.center - pulse_r, self.center - pulse_r,
            self.center + pulse_r, self.center + pulse_r,
            outline=core_color, width=1
        )

        # 3. Rotating Segmented Arc Spokes (Classic Arc Reactor)
        num_spokes = 12
        for i in range(num_spokes):
            theta = self.angle + (i * (2 * math.pi / num_spokes))
            x1 = self.center + r_inner * math.cos(theta)
            y1 = self.center + r_inner * math.sin(theta)
            x2 = self.center + (r_inner - 8) * math.cos(theta)
            y2 = self.center + (r_inner - 8) * math.sin(theta)
            self.canvas.create_line(x1, y1, x2, y2, fill=core_color, width=2)

        # 4. Core Ring
        self.canvas.create_oval(
            self.center - r_core, self.center - r_core,
            self.center + r_core, self.center + r_core,
            fill=Theme.CARD_BG, outline=core_color, width=3
        )

        # 5. Inner Arc Triangle / Core Nodes
        tri_r = 16
        pts = []
        for i in range(3):
            theta = self.angle * 0.5 + (i * (2 * math.pi / 3))
            pts.append(self.center + tri_r * math.cos(theta))
            pts.append(self.center + tri_r * math.sin(theta))
        self.canvas.create_polygon(pts, fill="", outline=core_color, width=2)

        # Center Glowing Node
        center_node_r = 8 + (self.pulse * 3)
        self.canvas.create_oval(
            self.center - center_node_r, self.center - center_node_r,
            self.center + center_node_r, self.center + center_node_r,
            fill=core_color, outline=""
        )

        self.after(33, self._animate)

    def destroy(self):
        self._is_animating = False
        super().destroy()


class AIAvatarGirlFace(ctk.CTkFrame):
    """
    3D Wireframe AI Girl Face Widget — tkinter port of the Pygame wireframe face.
    Full head mesh with 3D projection, Y/X auto-rotation, blinking, speaking waveform,
    facial feature curves (eyes, brows, nose, lips, jaw, hair, neck), and emotion badge.
    """

    # Color palette
    _BG   = "#03143A"
    _WIRE = "#41BEEF"
    _BRIGHT = "#7DEBFF"
    _DIM  = "#235A8C"

    def __init__(self, master, size: int = 160, **kwargs):
        super().__init__(master, fg_color=self._BG, **kwargs)

        self.canvas_w = size + 20
        self.canvas_h = size + 20

        self.avatar_controller = AIAvatarAnimationController()

        self.canvas = tk.Canvas(
            self,
            width=self.canvas_w,
            height=self.canvas_h,
            bg=self._BG,
            highlightthickness=0
        )
        self.canvas.pack(expand=True, fill="both")

        # State
        self.status = "ONLINE"
        self.current_emotion = "NEUTRAL"
        self.facial_params = self.avatar_controller.expression_presets["NEUTRAL"]

        # 3D rotation
        self.rot_y = 0.0
        self.rot_x = 0.0

        # Blink
        self.blink = 0.0
        self.blink_target = 0.0
        self.blink_timer = random.uniform(2, 5)

        self.last_tick = time.time()
        self._is_animating = True

        # Build head mesh and feature curves
        self._build_mesh()
        self._animate()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_status(self, status: str):
        self.status = status

    def react_to_text(self, text_response: str) -> str:
        emotion, params = self.avatar_controller.update_facial_reaction(text_response)
        self.current_emotion = emotion
        self.facial_params = params
        return emotion

    # ------------------------------------------------------------------
    # Mesh & Curve Builders
    # ------------------------------------------------------------------
    def _build_mesh(self):
        segments = 28
        ring_data = [
            (-220, 32, 38),
            (-185, 68, 54),
            (-145, 106, 80),
            (-95,  132, 100),
            (-40,  142, 108),
            (18,   140, 110),
            (75,   126, 100),
            (130,  108, 88),
            (175,  88,  68),
            (212,  58,  44),
        ]

        self.vertices = []
        self.rings = []
        for (y, rx, rz) in ring_data:
            ring = []
            for i in range(segments):
                a = 2 * math.pi * i / segments
                x = rx * math.cos(a)
                z = rz * math.sin(a)
                if y > 110:
                    x *= 0.90
                if y < -145:
                    x *= 1.04
                ring.append(len(self.vertices))
                self.vertices.append([x, y, z])
            self.rings.append(ring)

        # Face-forward deformation
        for i, (x, y, z) in enumerate(self.vertices):
            if -130 < y < 105:
                center = max(0, 1 - abs(x) / 150)
                self.vertices[i][2] = z + 22 * center

        # Edges
        self.edges = []
        for ring in self.rings:
            for i in range(segments):
                self.edges.append((ring[i], ring[(i + 1) % segments]))
        for r in range(len(self.rings) - 1):
            for i in range(segments):
                self.edges.append((self.rings[r][i], self.rings[r + 1][i]))

        # Feature curves
        def ellipse(cx, cy, cz, rx, ry, n=28, fwd=0):
            pts = []
            for i in range(n):
                a = 2 * math.pi * i / n
                pts.append((cx + rx * math.cos(a),
                             cy + ry * math.sin(a),
                             cz + fwd * math.cos(a)))
            return pts

        self.f_left_eye    = ellipse(-60, -32, 104, 40, 18, 28, 8)
        self.f_right_eye   = ellipse(60,  -32, 104, 40, 18, 28, 8)
        self.f_left_inner  = ellipse(-60, -32, 112, 20,  9, 20, 6)
        self.f_right_inner = ellipse(60,  -32, 112, 20,  9, 20, 6)

        self.f_left_brow  = [(-105, -74, 100), (-84, -84, 106), (-60, -87, 108), (-38, -77, 106)]
        self.f_right_brow = [(38,  -77, 106),  (60,  -87, 108), (84,  -84, 106), (105, -74, 100)]

        self.f_nose_l = [(-12, -16, 130), (-10, 12, 144), (-15, 42, 148), (-24, 60, 138)]
        self.f_nose_r = [(12,  -16, 130), (10,  12, 144), (15,  42, 148), (24,  60, 138)]
        self.f_nose_tip = ellipse(0, 62, 150, 26, 10, 22, 2)

        self.f_upper_lip = [(-46, 98, 124), (-25, 91, 130), (0, 98, 134), (25, 91, 130), (46, 98, 124)]
        self.f_lower_lip = ellipse(0, 108, 128, 44, 12, 26, 3)

        self.f_jaw_l = [(-110, 122, 80), (-94, 160, 64), (-66, 190, 50), (-30, 208, 42)]
        self.f_jaw_r = [(110,  122, 80), (94,  160, 64), (66,  190, 50), (30,  208, 42)]

        self.f_neck = [[(x, 205, 0), (x * 0.7, 310, 0)] for x in (-64, -38, 38, 64)]

        self.f_hair = []
        for side in (-1, 1):
            for j in range(5):
                pts = []
                for i in range(18):
                    t = i / 17
                    yv = -215 + t * 430
                    xv = side * (144 + 30 * math.sin(t * math.pi) + j * 8)
                    zv = 12 + 28 * math.cos(t * math.pi)
                    pts.append((xv, yv, zv))
                self.f_hair.append(pts)

    # ------------------------------------------------------------------
    # 3D Projection
    # ------------------------------------------------------------------
    def _project(self, p):
        x, y, z = p[0], p[1], p[2]

        # Scale to canvas size (base design ~450 units wide → canvas_w)
        s = self.canvas_w / 480.0

        cy_r, sy_r = math.cos(self.rot_y), math.sin(self.rot_y)
        x, z = x * cy_r - z * sy_r, x * sy_r + z * cy_r

        cx_r, sx_r = math.cos(self.rot_x), math.sin(self.rot_x)
        y, z = y * cx_r - z * sx_r, y * sx_r + z * cx_r

        cam = 700
        sc = cam / max(1, cam - z)

        sx = self.canvas_w / 2 + x * sc * s
        sy = self.canvas_h / 2 + y * sc * s
        return int(sx), int(sy), z

    # ------------------------------------------------------------------
    # Draw helpers
    # ------------------------------------------------------------------
    def _draw_curve(self, points, close=False, color=None, width=1):
        if color is None:
            color = self._BRIGHT
        projected = [self._project(p) for p in points]
        screen_pts = [(p[0], p[1]) for p in projected]
        for a, b in zip(screen_pts, screen_pts[1:]):
            self.canvas.create_line(a[0], a[1], b[0], b[1], fill=color, width=width)
        if close and len(screen_pts) > 1:
            self.canvas.create_line(screen_pts[-1][0], screen_pts[-1][1],
                                    screen_pts[0][0], screen_pts[0][1],
                                    fill=color, width=width)

    # ------------------------------------------------------------------
    # Main Render Loop
    # ------------------------------------------------------------------
    def _animate(self):
        if not self.winfo_exists() or not self._is_animating:
            return

        now = time.time()
        dt = max(0.016, now - self.last_tick)
        self.last_tick = now

        # Auto-rotate
        self.rot_y += dt * 0.18

        # Blink logic
        self.blink_timer -= dt
        if self.blink_timer <= 0:
            self.blink_target = 1.0
            self.blink_timer = random.uniform(2.5, 5.0)
        if self.blink_target > 0:
            self.blink += dt * 8
            if self.blink >= 1:
                self.blink = 0
                self.blink_target = 0

        # Theme color by status / emotion
        emotion_color = self.facial_params.get("color", self._BRIGHT)
        if self.status == "LISTENING":
            wire_color  = "#00E676"
            bright_color = "#00FF88"
        elif self.status == "THINKING":
            wire_color  = "#FFB300"
            bright_color = "#FFD740"
        elif self.status == "SPEAKING":
            wire_color  = emotion_color
            bright_color = "#FFFFFF"
        else:
            wire_color  = self._WIRE
            bright_color = self._BRIGHT

        self.canvas.delete("all")

        # Background radial grid rings
        cx_c, cy_c = self.canvas_w // 2, self.canvas_h // 2
        for r in range(int(self.canvas_w * 0.35), int(self.canvas_w * 0.70), int(self.canvas_w * 0.07)):
            self.canvas.create_oval(cx_c - r, cy_c - r, cx_c + r, cy_c + r,
                                    outline="#082D55", width=1)

        # Head mesh edges
        for a, b in self.edges:
            pa = self._project(self.vertices[a])
            pb = self._project(self.vertices[b])
            avg_z = (self.vertices[a][2] + self.vertices[b][2]) / 2
            col = wire_color if avg_z > 0 else self._DIM
            self.canvas.create_line(pa[0], pa[1], pb[0], pb[1], fill=col, width=1)

        # Eyes with blink scale
        blink_scale = max(0.05, 1.0 - self.blink)
        for eye_pts, inner_pts in [(self.f_left_eye, self.f_left_inner),
                                    (self.f_right_eye, self.f_right_inner)]:
            # Scale Y of each eye point toward eye center
            eye_cy = eye_pts[0][1]
            scaled_eye = [(p[0], eye_cy + (p[1] - eye_cy) * blink_scale, p[2]) for p in eye_pts]
            scaled_inner = [(p[0], eye_cy + (p[1] - eye_cy) * blink_scale, p[2]) for p in inner_pts]
            self._draw_curve(scaled_eye, close=True, color=bright_color, width=1)
            if blink_scale > 0.2:
                self._draw_curve(scaled_inner, close=True, color=bright_color, width=1)

        # Eyebrows — slant from emotion
        slant = self.facial_params.get("eyebrow_slant", 0.0)
        offset = slant * 10
        slanted_l_brow = [(p[0], p[1] + (1 if i < 2 else -1) * offset, p[2])
                          for i, p in enumerate(self.f_left_brow)]
        slanted_r_brow = [(p[0], p[1] + (1 if i >= 2 else -1) * offset, p[2])
                          for i, p in enumerate(self.f_right_brow)]
        self._draw_curve(slanted_l_brow, color=bright_color, width=2)
        self._draw_curve(slanted_r_brow, color=bright_color, width=2)

        # Nose
        self._draw_curve(self.f_nose_l, color=wire_color, width=1)
        self._draw_curve(self.f_nose_r, color=wire_color, width=1)
        self._draw_curve(self.f_nose_tip, close=True, color=bright_color, width=1)

        # Lips — emotion smile deform
        smile = self.facial_params.get("mouth_smile", 0.1)
        smile_lift = smile * 8
        deformed_upper = [(p[0], p[1] - smile_lift, p[2]) for p in self.f_upper_lip]
        self._draw_curve(deformed_upper, color=bright_color, width=1)
        self._draw_curve(self.f_lower_lip, close=True, color=bright_color, width=1)

        # Speaking waveform over mouth
        if self.status == "SPEAKING":
            for k in range(3):
                pts = []
                for i in range(22):
                    x = -52 + i * 5
                    y = 110 + math.sin(i * 0.85 + now * (7 + k)) * (4 + k * 2)
                    pts.append((x, y, 140 + k * 2))
                self._draw_curve(pts, color=bright_color, width=1)

        # Listening eye-scan line
        if self.status == "LISTENING":
            scan_y_local = -54 + ((math.sin(now * 2) + 1) / 2) * 44
            pa = self._project((-90, scan_y_local, 110))
            pb = self._project((90,  scan_y_local, 110))
            self.canvas.create_line(pa[0], pa[1], pb[0], pb[1], fill="#00FF88", width=1)

        # Jaw
        self._draw_curve(self.f_jaw_l, color=wire_color, width=1)
        self._draw_curve(self.f_jaw_r, color=wire_color, width=1)

        # Hair
        for pts in self.f_hair:
            self._draw_curve(pts, color=self._DIM, width=1)

        # Neck
        for pts in self.f_neck:
            self._draw_curve(pts, color=self._DIM, width=1)

        # Blush circles (2D overlay)
        if self.facial_params.get("blush", 0) > 0.3:
            self.canvas.create_oval(cx_c - 48, cy_c + 4, cx_c - 24, cy_c + 18,
                                    fill="#88103A", outline="")
            self.canvas.create_oval(cx_c + 24, cy_c + 4, cx_c + 48, cy_c + 18,
                                    fill="#88103A", outline="")

        # Emotion badge
        symbol = self.facial_params.get("symbol", "⚙️")
        self.canvas.create_text(
            cx_c, self.canvas_h - 10,
            text=f"{symbol} {self.current_emotion}",
            fill=bright_color,
            font=("Consolas", 8, "bold")
        )

        self.after(16, self._animate)

    def destroy(self):
        self._is_animating = False
        super().destroy()








    def set_status(self, status: str):
        self.status = status

    def react_to_text(self, text_response: str) -> str:
        emotion, params = self.avatar_controller.update_facial_reaction(text_response)
        self.current_emotion = emotion
        self.facial_params = params
        return emotion

    def _animate(self):
        if not self.winfo_exists() or not self._is_animating:
            return

        now = time.time()
        dt = max(0.016, now - self.last_tick)
        self.last_tick = now

        self.canvas.delete("all")

        cx, cy = self.center, self.center
        scale = self.size / 300.0  # Scale factor relative to 300px base design

        emotion_color = self.facial_params.get("color", Theme.CYAN_ACCENT)
        if self.status == "LISTENING":
            theme_color = Theme.SUCCESS
        elif self.status == "THINKING":
            theme_color = Theme.ALERT_WARN
        elif self.status == "SPEAKING":
            theme_color = emotion_color
        else:
            theme_color = emotion_color

        # -------------------------------------------------------------------
        # 1. Floating Cyber Particles
        # -------------------------------------------------------------------
        for p in self.particles:
            p[0] += p[2]
            p[3] += dt
            if p[0] > self.canvas_size:
                p[0] = 0
                p[1] = random.uniform(0, self.canvas_size)
            px, py_val = int(p[0]), int(p[1])
            self.canvas.create_rectangle(px, py_val, px + 1, py_val + 1, fill="#2878A0", outline="")

        # -------------------------------------------------------------------
        # 2. Blinking Logic
        # -------------------------------------------------------------------
        self.blink_timer -= dt
        if self.blink_timer <= 0 and self.blink_progress == 0:
            self.blink_progress = 0.001
        if self.blink_progress > 0:
            self.blink_progress += dt / self.blink_duration
            if self.blink_progress >= 1.0:
                self.blink_progress = 0.0
                self.blink_timer = random.uniform(2.0, 5.0)

        raw_eye_scale = self.facial_params.get("eye_open", 1.0)
        if self.blink_progress > 0:
            eye_scale = max(0.08, (1.0 - self.blink_progress) * raw_eye_scale)
        else:
            eye_scale = raw_eye_scale

        # -------------------------------------------------------------------
        # 3. Outer Glow Aura & Hair Polygon Silhouette
        # -------------------------------------------------------------------
        r_glow = int(100 * scale)
        self.canvas.create_oval(
            cx - r_glow, cy - r_glow,
            cx + r_glow, cy + r_glow,
            outline="#46D2FF", width=1
        )

        # Long flowing hair silhouette framing shoulders
        hair_rel = [
            (-105, -30), (-85, -110), (-35, -135), (35, -135),
            (85, -110), (105, -30), (115, 60), (110, 165),
            (85, 220), (65, 120), (50, -35), (-50, -35),
            (-65, 120), (-85, 220), (-110, 165), (-115, 60)
        ]
        hair_pts = []
        for hx, hy in hair_rel:
            hair_pts.extend([cx + (hx * scale), cy + (hy * scale)])

        self.canvas.create_polygon(hair_pts, fill="#192030", outline="#55D2FF", width=2)

        # -------------------------------------------------------------------
        # 4. Upper Body, Shoulders, Cyber Suit & V-Neck Contour
        # -------------------------------------------------------------------
        shoulder_w = int(190 * scale)
        chest_y = cy + int(70 * scale)
        bottom_y = self.canvas_size

        # Torso Polygon (Shoulders & Jacket Silhouette)
        torso_pts = [
            cx - (shoulder_w / 2), bottom_y,
            cx - int(70 * scale), chest_y + int(10 * scale),
            cx - int(28 * scale), chest_y - int(5 * scale),
            cx, chest_y + int(12 * scale),
            cx + int(28 * scale), chest_y - int(5 * scale),
            cx + int(70 * scale), chest_y + int(10 * scale),
            cx + (shoulder_w / 2), bottom_y
        ]

        # Draw Cyber Jacket (#182232) with Glowing Neon Collar Trim
        self.canvas.create_polygon(torso_pts, fill="#182232", outline=theme_color, width=2)

        # Inner V-Neck Undersuit (#0E1624)
        vneck_pts = [
            cx - int(22 * scale), chest_y - int(3 * scale),
            cx, chest_y + int(32 * scale),
            cx + int(22 * scale), chest_y - int(3 * scale)
        ]
        self.canvas.create_polygon(vneck_pts, fill="#0E1624", outline="")

        # Glowing Chest Core Emblem / Diamond Arc Core
        chest_core_y = chest_y + int(22 * scale)
        cd_r = int(7 * scale)
        self.canvas.create_polygon(
            [
                cx, chest_core_y - cd_r,
                cx + cd_r, chest_core_y,
                cx, chest_core_y + cd_r,
                cx - cd_r, chest_core_y
            ],
            fill=theme_color, outline="#D2FAFF", width=1
        )

        # Neck Column (#304052) & Cyber Choker Band
        neck_w, neck_h = int(50 * scale), int(38 * scale)
        neck_y = cy + int(48 * scale)
        self.canvas.create_rectangle(
            cx - (neck_w / 2), neck_y,
            cx + (neck_w / 2), neck_y + neck_h,
            fill="#304052", outline=""
        )
        self.canvas.create_line(
            cx - (neck_w / 2) - 2, neck_y + int(18 * scale),
            cx + (neck_w / 2) + 2, neck_y + int(18 * scale),
            fill=theme_color, width=2
        )

        # Face Oval Contour
        face_w, face_h = int(160 * scale), int(190 * scale)
        self.canvas.create_oval(
            cx - (face_w / 2), cy - (face_h / 2),
            cx + (face_w / 2), cy + (face_h / 2),
            fill="#2A3746", outline=theme_color, width=2
        )

        # -------------------------------------------------------------------
        # 5. Side AI Circuit Lines
        # -------------------------------------------------------------------
        for side in (-1, 1):
            sx1 = cx + side * int(78 * scale)
            sy1 = cy - int(20 * scale)
            sx2 = sx1 + side * int(14 * scale)
            self.canvas.create_line(sx1, sy1, sx2, sy1, fill="#46BEE6", width=2)
            self.canvas.create_line(sx2, sy1, sx2, sy1 + int(18 * scale), fill="#46BEE6", width=2)

        # -------------------------------------------------------------------
        # 6. Eyebrows & Eyes
        # -------------------------------------------------------------------
        eyebrow_slant = self.facial_params.get("eyebrow_slant", 0.0)
        brow_offset = int(eyebrow_slant * 6 * scale)

        # Eyebrows (Curved Lines)
        brow_y = cy - int(45 * scale)
        brow_w = int(40 * scale)

        # Left Eyebrow
        self.canvas.create_line(
            cx - int(55 * scale) - (brow_w / 2), brow_y - brow_offset,
            cx - int(55 * scale) + (brow_w / 2), brow_y + brow_offset,
            fill="#6EAEFF", width=2
        )
        # Right Eyebrow
        self.canvas.create_line(
            cx + int(55 * scale) - (brow_w / 2), brow_y + brow_offset,
            cx + int(55 * scale) + (brow_w / 2), brow_y - brow_offset,
            fill="#6EAEFF", width=2
        )

        # Eyes Sockets & Irises
        eye_dx = int(34 * scale)
        eye_y = cy - int(24 * scale)
        ew = int(38 * scale)
        eh = max(2, int(22 * scale * eye_scale))

        for ex in (cx - eye_dx, cx + eye_dx):
            # Eye Socket (dark background)
            self.canvas.create_oval(
                ex - (ew / 2), eye_y - (eh / 2),
                ex + (ew / 2), eye_y + (eh / 2),
                fill="#0F1823", outline=""
            )
            if eye_scale > 0.15:
                # Iris (Glowing Cyan/Theme)
                iw, ih = int(22 * scale), max(2, int(15 * scale * eye_scale))
                self.canvas.create_oval(
                    ex - (iw / 2), eye_y - (ih / 2),
                    ex + (iw / 2), eye_y + (ih / 2),
                    fill=theme_color, outline=""
                )
                # Pupil
                pr = max(1, int(5 * scale * eye_scale))
                self.canvas.create_oval(
                    ex - pr, eye_y - pr,
                    ex + pr, eye_y + pr,
                    fill="#050F19", outline=""
                )
                # Reflection Sparkle Dot
                sr = max(1, int(2 * scale))
                self.canvas.create_oval(
                    ex - pr - 1, eye_y - pr - 1,
                    ex - pr - 1 + sr * 2, eye_y - pr - 1 + sr * 2,
                    fill="#D2FAFF", outline=""
                )

        # -------------------------------------------------------------------
        # 6e. Sleek Cyber Sunglasses / Tinted Visor Shades
        # -------------------------------------------------------------------
        glass_w = int(46 * scale)
        glass_h = int(26 * scale)

        # Left Sunglasses Lens
        self.canvas.create_oval(
            cx - eye_dx - (glass_w / 2), eye_y - (glass_h / 2),
            cx - eye_dx + (glass_w / 2), eye_y + (glass_h / 2),
            fill="#080E18", outline=theme_color, width=2
        )
        # Right Sunglasses Lens
        self.canvas.create_oval(
            cx + eye_dx - (glass_w / 2), eye_y - (glass_h / 2),
            cx + eye_dx + (glass_w / 2), eye_y + (glass_h / 2),
            fill="#080E18", outline=theme_color, width=2
        )
        # Bridge connecting glasses
        self.canvas.create_line(
            cx - eye_dx + (glass_w / 2) - 2, eye_y - 2,
            cx + eye_dx - (glass_w / 2) + 2, eye_y - 2,
            fill=theme_color, width=3
        )
        # Glossy Light Reflection Gleam Lines
        self.canvas.create_line(
            cx - eye_dx - 12, eye_y - 7,
            cx - eye_dx + 4, eye_y + 7,
            fill="#D2FAFF", width=2
        )
        self.canvas.create_line(
            cx + eye_dx - 12, eye_y - 7,
            cx + eye_dx + 4, eye_y + 7,
            fill="#D2FAFF", width=2
        )

        # -------------------------------------------------------------------
        # 7. Eyelashes — Upper & Lower
        # -------------------------------------------------------------------
        lash_count = 6
        lash_len = int(6 * scale)
        for ex in (cx - eye_dx, cx + eye_dx):
            for li in range(lash_count):
                lx = ex - (ew / 2) + li * (ew / (lash_count - 1))
                top_y = eye_y - (eh / 2)
                # Upper lash fans upward
                lash_angle = math.pi * 0.25 + li * (math.pi * 0.5 / (lash_count - 1))
                lx2 = lx + lash_len * math.cos(lash_angle) * 0.6
                ly2 = top_y - lash_len * math.sin(lash_angle)
                self.canvas.create_line(lx, top_y, lx2, ly2, fill="#D2FAFF", width=1)
            # Lower lash dots
            for li in range(4):
                lx = ex - int(12 * scale) + li * int(8 * scale)
                self.canvas.create_oval(lx - 1, eye_y + (eh / 2), lx + 1, eye_y + (eh / 2) + 2,
                                        fill="#A0DAFF", outline="")

        # -------------------------------------------------------------------
        # 8. Nose — Refined Soft Tip with Flare
        # -------------------------------------------------------------------
        nose_bridge_top = cy - int(10 * scale)
        nose_tip_y = cy + int(18 * scale)

        # Nose bridge line (thin, subtle)
        self.canvas.create_line(cx, nose_bridge_top, cx, nose_tip_y - int(4 * scale),
                                fill="#4A90A8", width=1)
        # Nose tip rounded highlight
        nt_r = int(5 * scale)
        self.canvas.create_oval(cx - nt_r, nose_tip_y - nt_r,
                                cx + nt_r, nose_tip_y + nt_r,
                                fill="#3B6B80", outline="")
        # Nose highlight gleam
        self.canvas.create_oval(cx - 1, nose_tip_y - nt_r + 1,
                                cx + 2, nose_tip_y - nt_r + 3,
                                fill="#B0E8F8", outline="")
        # Nose flare arcs (nostrils)
        flare_off = int(9 * scale)
        for fside in (-1, 1):
            fx = cx + fside * flare_off
            self.canvas.create_arc(fx - int(5 * scale), nose_tip_y - int(4 * scale),
                                   fx + int(5 * scale), nose_tip_y + int(4 * scale),
                                   start=0, extent=180, style="arc", outline="#4A90A8", width=1)

        # -------------------------------------------------------------------
        # 9. Soft Facial Skin Shading & Cheek Glow
        # -------------------------------------------------------------------
        # Permanent soft cheek shimmer (always visible, subtle)
        cheek_r = int(16 * scale)
        for ex in (cx - eye_dx, cx + eye_dx):
            self.canvas.create_oval(
                ex - cheek_r, nose_tip_y - int(4 * scale) - (cheek_r // 2),
                ex + cheek_r, nose_tip_y - int(4 * scale) + cheek_r,
                fill="#33556E", outline=""
            )

        # Blush when emotion triggers
        blush = self.facial_params.get("blush", 0.0)
        always_blush = 0.18  # subtle always-on glow
        effective_blush = max(always_blush, blush)
        blush_r = int(13 * scale * effective_blush)
        for ex in (cx - eye_dx, cx + eye_dx):
            self.canvas.create_oval(
                ex - blush_r, nose_tip_y - int(2 * scale) - (blush_r // 2),
                ex + blush_r, nose_tip_y - int(2 * scale) + blush_r,
                fill="#A0204A" if blush > 0.5 else "#7D2040",
                outline=""
            )

        # -------------------------------------------------------------------
        # 10. Ear Studs / Cyber Earrings
        # -------------------------------------------------------------------
        ear_y = cy - int(10 * scale)
        ear_x_l = cx - int(74 * scale)
        ear_x_r = cx + int(74 * scale)
        stud_r = int(4 * scale)
        for ex in (ear_x_l, ear_x_r):
            self.canvas.create_oval(ex - stud_r, ear_y - stud_r,
                                    ex + stud_r, ear_y + stud_r,
                                    fill=theme_color, outline="#D2FAFF", width=1)
            # Dangle drop
            self.canvas.create_line(ex, ear_y + stud_r, ex, ear_y + stud_r + int(8 * scale),
                                    fill=theme_color, width=1)
            self.canvas.create_oval(ex - 2, ear_y + stud_r + int(8 * scale) - 2,
                                    ex + 2, ear_y + stud_r + int(8 * scale) + 2,
                                    fill="#D2FAFF", outline="")

        # -------------------------------------------------------------------
        # 11. Lips — Full Shape with Gloss Shimmer
        # -------------------------------------------------------------------
        mouth_smile = self.facial_params.get("mouth_smile", 0.1)
        mouth_y = cy + int(44 * scale)
        mw = int(46 * scale)
        mh_upper = int(9 * scale)
        mh_lower = int(11 * scale)

        if self.status == "SPEAKING":
            mouth_open = int(6 * scale + abs(math.sin(now * 10)) * 10 * scale)
        elif self.status == "THINKING":
            mouth_open = int(3 * scale)
        else:
            mouth_open = 0

        # Lower lip (fuller)
        self.canvas.create_arc(
            cx - (mw / 2), mouth_y,
            cx + (mw / 2), mouth_y + mh_lower + mouth_open,
            start=180, extent=180, style="chord",
            fill="#7B1C3C", outline=theme_color, width=1
        )
        # Upper lip (cupid's bow)
        self.canvas.create_arc(
            cx - (mw / 2), mouth_y - mh_upper,
            cx + (mw / 2), mouth_y + mh_upper,
            start=0, extent=180, style="chord",
            fill="#B0275A", outline=theme_color, width=1
        )
        # Cupid's bow center dip
        self.canvas.create_arc(
            cx - int(10 * scale), mouth_y - int(5 * scale),
            cx + int(10 * scale), mouth_y + int(5 * scale),
            start=180, extent=180, style="chord",
            fill="#2A3746", outline=""
        )
        # Lip gloss shimmer highlight
        self.canvas.create_oval(
            cx - int(8 * scale), mouth_y + int(2 * scale),
            cx + int(8 * scale), mouth_y + int(5 * scale),
            fill="#F0A0C0", outline=""
        )
        # Smile crease corners
        if mouth_smile >= 0:
            curve_h = max(2, int((8 * mouth_smile + 3) * scale))
            self.canvas.create_arc(
                cx - (mw / 2) + int(4 * scale), mouth_y - curve_h,
                cx + (mw / 2) - int(4 * scale), mouth_y + curve_h,
                start=200, extent=140, style="arc", outline=theme_color, width=1
            )
        else:
            curve_h = max(2, int((8 * abs(mouth_smile) + 3) * scale))
            self.canvas.create_arc(
                cx - (mw / 2) + int(4 * scale), mouth_y - curve_h,
                cx + (mw / 2) - int(4 * scale), mouth_y + curve_h,
                start=20, extent=140, style="arc", outline=theme_color, width=1
            )

        # -------------------------------------------------------------------
        # 12. Beauty Mark / Mole — above lip right side
        # -------------------------------------------------------------------
        bm_x = cx + int(28 * scale)
        bm_y = mouth_y - int(10 * scale)
        self.canvas.create_oval(bm_x - 2, bm_y - 2, bm_x + 2, bm_y + 2,
                                fill="#3A1020", outline="")

        # -------------------------------------------------------------------
        # 13. Emotion Badge Text
        # -------------------------------------------------------------------
        symbol = self.facial_params.get("symbol", "⚙️")
        self.canvas.create_text(
            cx, cy + (face_h / 2) + 12,
            text=f"{symbol} {self.current_emotion}",
            fill=theme_color,
            font=("Consolas", 8, "bold")
        )

        self.after(33, self._animate)

    def destroy(self):
        self._is_animating = False
        super().destroy()


class AnimatedAICore(ctk.CTkFrame):
    """Parent Container housing Iron Man Arc Reactor on the Left + Pygame-Style AI Girl Face on the Right."""

    def __init__(self, master, size: int = 140, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # 1. Left: Classic Iron Man Arc Reactor
        self.arc_reactor = IronManArcReactor(self, size=size)
        self.arc_reactor.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")

        # 2. Right: Pygame-Style Cyber AI Girl Avatar Face
        self.girl_face = AIAvatarGirlFace(self, size=size)
        self.girl_face.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")

    def set_status(self, status: str):
        """Propagate status changes to both Arc Reactor and Girl Avatar Face."""
        self.arc_reactor.set_status(status)
        self.girl_face.set_status(status)

    def react_to_text(self, text_response: str) -> str:
        """Trigger facial reaction on the AI Girl Avatar Face."""
        return self.girl_face.react_to_text(text_response)

    def set_emotion(self, emotion: str):
        """Set facial emotion on Girl Avatar Face."""
        if hasattr(self.girl_face, 'avatar_controller'):
            if emotion in self.girl_face.avatar_controller.expression_presets:
                self.girl_face.current_emotion = emotion
                self.girl_face.facial_params = self.girl_face.avatar_controller.expression_presets[emotion]
