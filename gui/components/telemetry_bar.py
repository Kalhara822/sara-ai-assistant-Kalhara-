"""
Hardware Telemetry Display Component (CPU, RAM, Disk Gauges)
Periodic non-blocking monitoring widget updating UI stats every second.
"""

import customtkinter as ctk
from gui.theme import Theme
from utils.system_info import SystemInfo

class TelemetryBar(ctk.CTkFrame):
    """Telemetry status bar rendering CPU, RAM, and Disk metrics."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            **kwargs
        )
        
        # Configure Grid Layout (3 columns for CPU, RAM, DISK)
        self.columnconfigure((0, 1, 2), weight=1, uniform="telemetry")
        self.rowconfigure(0, weight=1)

        # 1. CPU Gauge
        self.cpu_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cpu_frame.grid(row=0, column=0, padx=Theme.PADDING_MEDIUM, pady=Theme.PADDING_SMALL, sticky="ew")
        
        self.cpu_title = ctk.CTkLabel(self.cpu_frame, text="CPU USAGE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED)
        self.cpu_title.pack(anchor="w")
        
        self.cpu_val = ctk.CTkLabel(self.cpu_frame, text="0%", font=Theme.FONT_SUBHEADER, text_color=Theme.CYAN_ACCENT)
        self.cpu_val.pack(anchor="w")
        
        self.cpu_bar = ctk.CTkProgressBar(self.cpu_frame, height=6, progress_color=Theme.CYAN_ACCENT, fg_color=Theme.BG_DARK)
        self.cpu_bar.set(0.0)
        self.cpu_bar.pack(fill="x", pady=(2, 0))

        # 2. RAM Gauge
        self.ram_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ram_frame.grid(row=0, column=1, padx=Theme.PADDING_MEDIUM, pady=Theme.PADDING_SMALL, sticky="ew")

        self.ram_title = ctk.CTkLabel(self.ram_frame, text="RAM USAGE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED)
        self.ram_title.pack(anchor="w")

        self.ram_val = ctk.CTkLabel(self.ram_frame, text="0.0 / 12.0 GB", font=Theme.FONT_SUBHEADER, text_color=Theme.BLUE_ACCENT)
        self.ram_val.pack(anchor="w")

        self.ram_bar = ctk.CTkProgressBar(self.ram_frame, height=6, progress_color=Theme.BLUE_ACCENT, fg_color=Theme.BG_DARK)
        self.ram_bar.set(0.0)
        self.ram_bar.pack(fill="x", pady=(2, 0))

        # 3. DISK Gauge
        self.disk_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.disk_frame.grid(row=0, column=2, padx=Theme.PADDING_MEDIUM, pady=Theme.PADDING_SMALL, sticky="ew")

        self.disk_title = ctk.CTkLabel(self.disk_frame, text="DISK FREE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED)
        self.disk_title.pack(anchor="w")

        self.disk_val = ctk.CTkLabel(self.disk_frame, text="0 GB", font=Theme.FONT_SUBHEADER, text_color=Theme.TEXT_MAIN)
        self.disk_val.pack(anchor="w")

        self.disk_bar = ctk.CTkProgressBar(self.disk_frame, height=6, progress_color=Theme.CYAN_ACCENT, fg_color=Theme.BG_DARK)
        self.disk_bar.set(0.0)
        self.disk_bar.pack(fill="x", pady=(2, 0))

        self._is_running = True
        self._update_metrics()

    def _update_metrics(self):
        """Fetch system info and update progress bars."""
        if not self.winfo_exists() or not self._is_running:
            return

        try:
            cpu_pct = SystemInfo.get_cpu_usage()
            mem_info = SystemInfo.get_memory_info()
            disk_info = SystemInfo.get_disk_info()

            # Update CPU with dynamic color (Red for 90-100%, Amber for 75-89%, Cyan for normal)
            self.cpu_bar.set(min(1.0, cpu_pct / 100.0))
            if cpu_pct >= 90.0:
                self.cpu_val.configure(text=f"{cpu_pct:.1f}%", text_color="#FF1744")
                self.cpu_bar.configure(progress_color="#FF1744")
                self.cpu_title.configure(text="CPU [CRITICAL]", text_color="#FF1744")
            elif cpu_pct >= 75.0:
                self.cpu_val.configure(text=f"{cpu_pct:.1f}%", text_color="#FF9E80")
                self.cpu_bar.configure(progress_color="#FF9E80")
                self.cpu_title.configure(text="CPU [HIGH]", text_color="#FF9E80")
            else:
                self.cpu_val.configure(text=f"{cpu_pct:.1f}%", text_color=Theme.CYAN_ACCENT)
                self.cpu_bar.configure(progress_color=Theme.CYAN_ACCENT)
                self.cpu_title.configure(text="CPU USAGE", text_color=Theme.TEXT_MUTED)

            # Update RAM with dynamic color
            mem_pct = mem_info.get('percent', 0.0)
            self.ram_val.configure(text=f"{mem_info['used_gb']} / {mem_info['total_gb']} GB")
            self.ram_bar.set(min(1.0, mem_pct / 100.0))
            if mem_pct >= 90.0:
                self.ram_val.configure(text_color="#FF1744")
                self.ram_bar.configure(progress_color="#FF1744")
                self.ram_title.configure(text="RAM [CRITICAL]", text_color="#FF1744")
            elif mem_pct >= 80.0:
                self.ram_val.configure(text_color="#FF9E80")
                self.ram_bar.configure(progress_color="#FF9E80")
                self.ram_title.configure(text="RAM [HIGH]", text_color="#FF9E80")
            else:
                self.ram_val.configure(text_color=Theme.BLUE_ACCENT)
                self.ram_bar.configure(progress_color=Theme.BLUE_ACCENT)
                self.ram_title.configure(text="RAM USAGE", text_color=Theme.TEXT_MUTED)

            # Update Disk
            self.disk_val.configure(text=f"{disk_info['free_gb']} GB Free")
            self.disk_bar.set(min(1.0, (100.0 - disk_info['percent']) / 100.0))
        except Exception:
            pass

        # Schedule refresh every 1000ms
        self.after(1000, self._update_metrics)

    def destroy(self):
        self._is_running = False
        super().destroy()
