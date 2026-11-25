"""
Master Application Window for SARA AI Assistant
CustomTkinter JARVIS-themed Desktop HUD Window Layout
"""

import threading
import customtkinter as ctk
from config import config
from gui.theme import Theme
from gui.components.header_widget import HeaderWidget
from gui.components.telemetry_bar import TelemetryBar
from gui.components.animated_core import AnimatedAICore
from gui.components.waveform import WaveformVisualizer
from gui.components.quick_actions import QuickActionsBar
from gui.components.chat_history import ChatHistoryView
from gui.components.typing_area import TypingInputArea
from gui.components.plugin_panel import PluginManagerPanel
from gui.components.routines_panel import RoutinesPanel
from voice.orchestrator import VoiceOrchestrator
from utils.resource_guard import ResourceGuard
from utils.tray_manager import SystemTrayManager
from utils.logger import logger

class SARAMainWindow(ctk.CTk):
    """Main Desktop UI Application Window for SARA AI."""

    def __init__(self):
        super().__init__()

        # Window Metadata & Geometry
        self.title(config.ui.APP_TITLE)
        self.geometry(f"{config.ui.WINDOW_WIDTH}x{config.ui.WINDOW_HEIGHT}")
        self.minsize(config.ui.MIN_WIDTH, config.ui.MIN_HEIGHT)
        self.configure(fg_color=Theme.BG_DARK)

        # Set CustomTkinter Appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Configure Root Grid (2 main columns: Left Visual/Control Pane, Right Chat Pane)
        self.columnconfigure(0, weight=4, uniform="root")  # Left Control HUD
        self.columnconfigure(1, weight=5, uniform="root")  # Right Chat Stream
        self.rowconfigure(0, weight=0)                      # Header Bar
        self.rowconfigure(1, weight=0)                      # Telemetry Gauge Bar
        self.rowconfigure(2, weight=1)                      # Central Workspace
        self.rowconfigure(3, weight=0)                      # Quick Actions & Input Area

        # Build UI Components
        self._build_header()
        self._build_telemetry()
        self._build_left_control_pane()
        self._build_right_chat_pane()
        self._build_bottom_input_pane()

        # Initialize Voice Orchestrator
        self._voice = VoiceOrchestrator(
            on_command_received=self._handle_user_command,
            on_status_change=lambda s: self.after(0, lambda: self.set_ai_status(s)),
            on_audio_level=None
        )

        # Initialize SARA Core Engine (lazy - imports happen on first use)
        self._engine = None
        self.after(500, self._init_sara_engine)

        # Initialize Hardware Resource Guard
        self._guard = ResourceGuard(
            on_warning_callback=lambda msg: self.after(
                0, lambda: self.header.show_system_notice(msg)
            )
        )
        self._guard.start()

        # Initialize System Tray Manager
        self._tray = SystemTrayManager(
            on_show=self._show_from_tray,
            on_exit=self.on_close,
            on_trim_memory=lambda: self._handle_user_command("trim memory")
        )
        self._tray.start()

        # Bind close button to hide to tray or exit
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        logger.info("SARA Master GUI Window initialized successfully.")

    def _build_header(self):
        """Top Status & Clock Header."""
        self.header = HeaderWidget(self, on_voice_change=self._handle_voice_change)
        self.header.grid(row=0, column=0, columnspan=2, padx=Theme.PADDING_MEDIUM, pady=(Theme.PADDING_MEDIUM, 0), sticky="ew")

    def _handle_voice_change(self, profile_key: str):
        """Switch voice profile from header dropdown or command."""
        cmd_text = f"switch voice to {profile_key}"
        self._handle_user_command(cmd_text)

    def _build_telemetry(self):
        """Hardware Telemetry Bar."""
        self.telemetry = TelemetryBar(self)
        self.telemetry.grid(row=1, column=0, columnspan=2, padx=Theme.PADDING_MEDIUM, pady=Theme.PADDING_MEDIUM, sticky="ew")

    def _build_left_control_pane(self):
        """Left HUD Container — tabbed: [Core View] | [Plugin Manager]."""
        self.left_pane = ctk.CTkFrame(
            self,
            fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS
        )
        self.left_pane.grid(row=2, column=0, padx=(Theme.PADDING_MEDIUM, Theme.PADDING_SMALL), pady=0, sticky="nsew")
        self.left_pane.rowconfigure(1, weight=1)
        self.left_pane.columnconfigure(0, weight=1)

        # ── Tab Switcher Bar ──────────────────────────────────────────────
        tab_bar = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        tab_bar.grid(row=0, column=0, padx=8, pady=(8, 0), sticky="ew")

        self._tab_core_btn = ctk.CTkButton(
            tab_bar, text="CORE",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=10, weight="bold"),
            fg_color=Theme.ACCENT_CYAN, text_color=Theme.BG_DARK,
            hover_color=Theme.ACCENT_BLUE,
            width=70, height=26, corner_radius=6,
            command=self._show_core_view
        )
        self._tab_core_btn.pack(side="left", padx=(0, 3))

        self._tab_plugin_btn = ctk.CTkButton(
            tab_bar, text="PLUGINS",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=10, weight="bold"),
            fg_color=Theme.SURFACE, text_color=Theme.TEXT_MUTED,
            hover_color=Theme.ACCENT_BLUE,
            width=70, height=26, corner_radius=6,
            command=self._show_plugin_view
        )
        self._tab_plugin_btn.pack(side="left", padx=(0, 3))

        self._tab_routines_btn = ctk.CTkButton(
            tab_bar, text="ROUTINES",
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=10, weight="bold"),
            fg_color=Theme.SURFACE, text_color=Theme.TEXT_MUTED,
            hover_color=Theme.ACCENT_BLUE,
            width=70, height=26, corner_radius=6,
            command=self._show_routines_view
        )
        self._tab_routines_btn.pack(side="left")

        # ── Core View (Arc Reactor + Waveform) ────────────────────────────
        self._core_frame = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        self._core_frame.grid(row=1, column=0, sticky="nsew")

        self.core_widget = AnimatedAICore(self._core_frame, size=160)
        self.core_widget.pack(expand=True, fill="both", pady=(Theme.PADDING_LARGE, 0))

        self.waveform_widget = WaveformVisualizer(self._core_frame, width=320, height=45)
        self.waveform_widget.pack(pady=Theme.PADDING_MEDIUM)

        # ── Plugin Manager View ───────────────────────────────────────────
        self.plugin_panel = PluginManagerPanel(self.left_pane)
        # Initially hidden—shown on PLUGINS tab click

        # ── Routines View ───────────────────────────────────────────────
        self.routines_panel = RoutinesPanel(
            self.left_pane,
            on_run_routine=self._handle_run_routine
        )
        # Initially hidden—shown on ROUTINES tab click

    def _build_right_chat_pane(self):
        """Right Conversation History Stream."""
        self.chat_view = ChatHistoryView(
            self,
            fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS
        )
        self.chat_view.grid(row=2, column=1, padx=(Theme.PADDING_SMALL, Theme.PADDING_MEDIUM), pady=0, sticky="nsew")

    def _build_bottom_input_pane(self):
        """Bottom Control Container (Quick Actions + Text/Voice Input Bar)."""
        self.bottom_container = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_container.grid(row=3, column=0, columnspan=2, padx=Theme.PADDING_MEDIUM, pady=Theme.PADDING_MEDIUM, sticky="ew")

        # Quick Actions Bar
        self.quick_actions = QuickActionsBar(
            self.bottom_container,
            on_action_clicked=self._handle_user_command
        )
        self.quick_actions.pack(fill="x", pady=(0, Theme.PADDING_SMALL))

        # Typing & Voice Input Area
        self.input_area = TypingInputArea(
            self.bottom_container,
            on_send_text=self._handle_user_command,
            on_toggle_voice=self._handle_voice_toggle
        )
        self.input_area.pack(fill="x")

    def _show_core_view(self):
        """Switch left pane to Arc Reactor Core view."""
        self.plugin_panel.grid_forget()
        self.routines_panel.grid_forget()
        self._core_frame.grid(row=1, column=0, sticky="nsew")
        self._tab_core_btn.configure(fg_color=Theme.ACCENT_CYAN, text_color=Theme.BG_DARK)
        self._tab_plugin_btn.configure(fg_color=Theme.SURFACE, text_color=Theme.TEXT_MUTED)
        self._tab_routines_btn.configure(fg_color=Theme.SURFACE, text_color=Theme.TEXT_MUTED)

    def _show_plugin_view(self):
        """Switch left pane to Plugin Manager view."""
        self._core_frame.grid_forget()
        self.routines_panel.grid_forget()
        self.plugin_panel.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._tab_core_btn.configure(fg_color=Theme.SURFACE, text_color=Theme.TEXT_MUTED)
        self._tab_plugin_btn.configure(fg_color=Theme.ACCENT_CYAN, text_color=Theme.BG_DARK)
        self._tab_routines_btn.configure(fg_color=Theme.SURFACE, text_color=Theme.TEXT_MUTED)

    def _show_routines_view(self):
        """Switch left pane to Smart Routines panel."""
        self._core_frame.grid_forget()
        self.plugin_panel.grid_forget()
        self.routines_panel.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._tab_core_btn.configure(fg_color=Theme.SURFACE, text_color=Theme.TEXT_MUTED)
        self._tab_plugin_btn.configure(fg_color=Theme.SURFACE, text_color=Theme.TEXT_MUTED)
        self._tab_routines_btn.configure(fg_color=Theme.ACCENT_CYAN, text_color=Theme.BG_DARK)

    def _handle_run_routine(self, routine_name: str):
        """Trigger a routine from the GUI panel via the engine."""
        cmd_text = f"run routine {routine_name}"
        self.chat_view.add_message("User", cmd_text, is_user=True)
        self.set_ai_status("THINKING")
        if self._engine:
            threading.Thread(
                target=self._engine.process_command,
                args=(cmd_text,),
                name="RoutineWorker",
                daemon=True
            ).start()
        else:
            self.after(200, lambda: self._on_engine_response(
                "Engine not ready yet. Please wait a moment.", ""
            ))

    def _init_sara_engine(self):
        """Initialize SARA Engine in background thread to avoid blocking GUI startup."""
        def _load():
            try:
                from sara_engine import SARAEngine
                self._engine = SARAEngine(
                    on_response=lambda text, speech: self.after(
                        0, lambda t=text, s=speech: self._on_engine_response(t, s)
                    )
                )
                self._engine.set_tts_engine(self._voice.tts)
                status = self._engine.get_ai_status()
                ai_ok = status["ollama_available"]
                n_cmds = status['registered_commands']
                plugins = status.get("plugins", [])
                ai_label = "Connected" if ai_ok else "Offline (run: ollama serve)"
                ai_msg = (
                    f"SARA online. {n_cmds} commands | "
                    f"{len(plugins)} plugins loaded | AI: {ai_label}"
                )
                self.after(0, lambda: self.header.show_system_notice(ai_msg))
                self.after(0, lambda p=plugins: self.plugin_panel.refresh(p))
                # Refresh routines panel with built-in + custom routines
                try:
                    from automation.routines import RoutineEngine
                    _re = RoutineEngine(dispatch_callback=lambda a, p: None)
                    routines = _re.list_routines()
                    self.after(0, lambda r=routines: self.routines_panel.refresh(r))
                except Exception as _re_err:
                    logger.warning(f"Could not load routines for panel: {_re_err}")

                # Always speak greeting voice on startup
                self.after(500, lambda: self._voice.speak("Hey sir, targeting systems online, ready to serve."))
                logger.info(f"SARAEngine loaded. Ollama: {ai_ok}, Plugins: {len(plugins)}")
            except Exception as e:
                logger.error(f"Failed to initialize SARAEngine: {e}", exc_info=True)
                self.after(500, lambda: self._voice.speak("Hey sir, targeting systems online, ready to serve."))

        threading.Thread(target=_load, name="EngineLoader", daemon=True).start()

    def _handle_user_command(self, command_text: str):
        """Process command submitted by user from typing box or quick actions."""
        logger.info(f"User command received: '{command_text}'")

        # Display user message bubble
        self.chat_view.add_message(sender="User", text=command_text, is_user=True)

        # Set UI status to thinking
        self.set_ai_status("THINKING")

        # Route through SARA Engine (non-blocking background thread)
        if self._engine:
            threading.Thread(
                target=self._engine.process_command,
                args=(command_text,),
                name="CommandWorker",
                daemon=True
            ).start()
        else:
            # Engine still loading
            self.after(300, lambda: self._on_engine_response(
                "I'm still initializing my systems. Please try again in a moment.",
                "I'm still initializing, please wait a moment."
            ))

    def _on_engine_response(self, response_text: str, speech_text: str):
        """Called on the main thread when SARAEngine returns a response."""
        self.chat_view.add_message(sender="SARA", text=response_text, is_user=False)
        if hasattr(self, 'core_widget') and self.core_widget:
            self.core_widget.react_to_text(response_text)
        self._voice.speak(speech_text)
        self.set_ai_status("ONLINE")

    def _show_from_tray(self):
        """Restore window from System Tray."""
        self.after(0, self.deiconify)
        self.after(0, self.focus_force)

    def on_close(self) -> None:
        """Clean shutdown hook."""
        if hasattr(self, "_guard") and self._guard:
            self._guard.stop()
        if hasattr(self, "_tray") and self._tray:
            self._tray.stop()
        self._voice.stop_wake_word_mode()
        self.destroy()

    def _handle_voice_toggle(self):
        """Handle voice microphone button click — triggers real listen cycle."""
        if self.input_area.is_listening:
            # Start real voice listening
            self._voice.listen_once()
        else:
            # Stop voice if toggled off
            self._voice.stop_speaking()
            self.set_ai_status("ONLINE")
            self.waveform_widget.set_active(False)

    def set_ai_status(self, status: str):
        """Update system status across all HUD widgets."""
        self.header.set_status(status)
        self.core_widget.set_status(status)
        if hasattr(self.waveform_widget, 'set_status'):
            self.waveform_widget.set_status(status)
        if status in ("LISTENING", "SPEAKING", "THINKING"):
            self.waveform_widget.set_active(True)
        else:
            self.waveform_widget.set_active(False)
