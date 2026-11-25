"""
SARA Core Engine
The master orchestrator that coordinates:
  AI Intent Parsing (Ollama) -> Command Dispatch -> Memory -> TTS Response

This is the central brain of SARA. The GUI and Voice modules both call into
this engine which returns structured results and spoken responses.
"""

import re
import time
from typing import Optional, Dict, Any, List, Callable
from ai.ollama_engine import OllamaIntentEngine
from ai.schemas import IntentResponse
from ai.gemini_engine import GeminiAIEngine
from commands.dispatcher import CommandDispatcher
from database.memory_manager import MemoryManager
from plugins.base import PluginManager
from plugins.loader import PluginLoader
from utils.logger import logger


class SARAEngine:
    """
    Central AI + Command + Memory coordinator for SARA.
    Accepts text commands from GUI or Voice input, resolves intent via Ollama,
    executes the appropriate command, and returns a structured response.
    """

    def __init__(self, on_response: Optional[Callable[[str, str], None]] = None):
        """
        Args:
            on_response: Callback(text: str, speech: str) called with SARA's reply.
                         text = displayed in GUI chat, speech = spoken via TTS.
        """
        self._ai = OllamaIntentEngine()
        self._gemini = GeminiAIEngine()
        self._dispatcher = CommandDispatcher()
        self._memory = MemoryManager()
        self._plugin_manager = PluginManager()
        self._on_response = on_response
        self._session_id = "default"
        self._plugin_summary: List[Dict[str, Any]] = []

        self._register_all_commands()
        self._load_plugins()
        logger.info("SARAEngine fully initialized.")

    # -----------------------------------------------------------------------
    # Command Registration
    # -----------------------------------------------------------------------

    def _register_all_commands(self) -> None:
        """Auto-register all built-in command handlers."""
        from commands.app_launcher import OpenApplicationCommand, CloseApplicationCommand
        from commands.folder_commands import OpenFolderCommand
        from commands.system_control import (
            ScreenshotCommand, LockPCCommand, ShutdownCommand,
            RestartCommand, SleepCommand, EmptyRecycleBinCommand
        )
        from commands.media_control import (
            SetVolumeCommand, IncreaseVolumeCommand, DecreaseVolumeCommand,
            MuteVolumeCommand, SetBrightnessCommand, IncreaseBrightnessCommand,
            DecreaseBrightnessCommand
        )
        from commands.browser_search import (
            SearchGoogleCommand, SearchYouTubeCommand, OpenWebsiteCommand,
            OpenLinkedInCommand, SearchWikipediaCommand, CheckWeatherCommand,
            DownloadFileCommand
        )
        from commands.system_telemetry import (
            GetCPUUsageCommand, GetRAMUsageCommand, GetDiskUsageCommand,
            GetBatteryStatusCommand, GetNetworkStatusCommand
        )
        from commands.memory_commands import RememberNoteCommand, RecallMemoryCommand, SetReminderCommand
        from commands.health_commands import TrimMemoryCommand, GetSystemHealthCommand

        # ── New command modules ──────────────────────────────────────────────
        from commands.power_commands import (
            HibernateCommand, CancelShutdownCommand, ShutdownAfterCommand,
            RestartAfterCommand, CheckPowerStatusCommand, CheckUptimeCommand
        )
        from commands.audio_commands import (
            GetVolumeLevelCommand, ChangeAudioOutputCommand,
            IncreaseMicVolumeCommand, DecreaseMicVolumeCommand,
            MuteMicrophoneCommand, UnmuteMicrophoneCommand, UnmuteVolumeCommand
        )
        from commands.display_commands import (
            GetBrightnessLevelCommand, ChangeResolutionCommand,
            EnableNightLightCommand, DisableNightLightCommand,
            DetectMonitorsCommand, SwitchDisplayModeCommand, GetDisplayInfoCommand
        )
        from commands.network_commands import (
            WiFiOnCommand, WiFiOffCommand, ShowWifiNetworksCommand,
            ConnectWifiCommand, DisconnectWifiCommand, CheckInternetCommand,
            ShowIPAddressCommand, ShowMACAddressCommand,
            TestNetworkSpeedCommand, OpenNetworkSettingsCommand
        )
        from commands.bluetooth_commands import (
            BluetoothOnCommand, BluetoothOffCommand, ShowBluetoothDevicesCommand,
            ConnectBluetoothCommand, OpenBluetoothSettingsCommand
        )
        from commands.file_commands import (
            CreateFolderCommand, RenameFileCommand, DeleteFileCommand,
            MoveFileCommand, CopyFileCommand, SearchFilesCommand,
            ShowRecentFilesCommand, CompressFilesCommand, ExtractZipCommand
        )
        from commands.monitor_commands import (
            ShowRunningAppsCommand, KillProcessCommand, GetCPUTemperatureCommand,
            GetLaptopSpecsCommand, GetWindowsVersionCommand, GetAvailableStorageCommand,
            ClearTempFilesCommand, RecordScreenCommand, StopRecordingCommand,
            StartScreenSharingCommand
        )

        from commands.voice_commands import SwitchVoiceCommand

        self._switch_voice_cmd = SwitchVoiceCommand()

        all_commands = [
            # App control
            OpenApplicationCommand(), CloseApplicationCommand(),
            OpenFolderCommand(),
            # Voice profiles
            self._switch_voice_cmd,
            # System
            ScreenshotCommand(), LockPCCommand(),
            ShutdownCommand(), RestartCommand(), SleepCommand(), EmptyRecycleBinCommand(),
            # Power (new)
            HibernateCommand(), CancelShutdownCommand(), ShutdownAfterCommand(),
            RestartAfterCommand(), CheckPowerStatusCommand(), CheckUptimeCommand(),
            # Audio
            SetVolumeCommand(), IncreaseVolumeCommand(), DecreaseVolumeCommand(),
            MuteVolumeCommand(), UnmuteVolumeCommand(),
            GetVolumeLevelCommand(), ChangeAudioOutputCommand(),
            IncreaseMicVolumeCommand(), DecreaseMicVolumeCommand(),
            MuteMicrophoneCommand(), UnmuteMicrophoneCommand(),
            # Display
            SetBrightnessCommand(), IncreaseBrightnessCommand(), DecreaseBrightnessCommand(),
            GetBrightnessLevelCommand(), ChangeResolutionCommand(),
            EnableNightLightCommand(), DisableNightLightCommand(),
            DetectMonitorsCommand(), SwitchDisplayModeCommand(), GetDisplayInfoCommand(),
            # Network
            WiFiOnCommand(), WiFiOffCommand(), ShowWifiNetworksCommand(),
            ConnectWifiCommand(), DisconnectWifiCommand(), CheckInternetCommand(),
            ShowIPAddressCommand(), ShowMACAddressCommand(),
            TestNetworkSpeedCommand(), OpenNetworkSettingsCommand(),
            # Bluetooth
            BluetoothOnCommand(), BluetoothOffCommand(), ShowBluetoothDevicesCommand(),
            ConnectBluetoothCommand(), OpenBluetoothSettingsCommand(),
            # File management
            CreateFolderCommand(), RenameFileCommand(), DeleteFileCommand(),
            MoveFileCommand(), CopyFileCommand(), SearchFilesCommand(),
            ShowRecentFilesCommand(), CompressFilesCommand(), ExtractZipCommand(),
            # Browser
            SearchGoogleCommand(), SearchYouTubeCommand(), OpenWebsiteCommand(),
            OpenLinkedInCommand(), SearchWikipediaCommand(), CheckWeatherCommand(),
            DownloadFileCommand(),
            # System telemetry
            GetCPUUsageCommand(), GetRAMUsageCommand(), GetDiskUsageCommand(),
            GetBatteryStatusCommand(), GetNetworkStatusCommand(),
            # System monitor (new)
            ShowRunningAppsCommand(), KillProcessCommand(), GetCPUTemperatureCommand(),
            GetLaptopSpecsCommand(), GetWindowsVersionCommand(), GetAvailableStorageCommand(),
            ClearTempFilesCommand(), RecordScreenCommand(), StopRecordingCommand(),
            StartScreenSharingCommand(),
            # Memory & health
            RememberNoteCommand(), RecallMemoryCommand(), SetReminderCommand(),
            TrimMemoryCommand(), GetSystemHealthCommand(),
        ]

        for cmd in all_commands:
            self._dispatcher.register(cmd)

        logger.info(f"Registered {len(all_commands)} built-in commands.")

    def _load_plugins(self) -> None:
        """Run plugin auto-discovery and register all found plugins."""
        loader = PluginLoader(
            dispatcher=self._dispatcher,
            plugin_manager=self._plugin_manager
        )
        result = loader.discover_and_load()
        self._plugin_summary = self._plugin_manager.list_plugins()
        logger.info(
            f"Plugin loader: {len(result['loaded'])} loaded, "
            f"{len(result['failed'])} failed "
            f"out of {result['total']} discovered."
        )
        if result["failed"]:
            for fail in result["failed"]:
                logger.warning(f"  [Plugin FAILED] {fail['file']}: {fail['error']}")

    # -----------------------------------------------------------------------
    # Public Interface
    # -----------------------------------------------------------------------

    def process_command(self, user_input: str) -> Dict[str, Any]:
        """
        Full pipeline: parse intent → execute command → store memory → return result.
        This is the primary entry point from GUI and Voice modules.
        """
        # Check for compound commands ("open chrome and go to youtube", "open whatsapp and take screenshot")
        if " and " in user_input.lower() or " then " in user_input.lower():
            parts = [p.strip() for p in re.split(r"\s+(?:and|then)\s+", user_input, flags=re.IGNORECASE) if p.strip()]
            if len(parts) > 1:
                logger.info(f"[SARAEngine] Splitting compound command into {len(parts)} steps: {parts}")
                last_result = {}
                messages = []
                speeches = []
                for p in parts:
                    res = self._process_single_command(p)
                    last_result = res
                    if res.get("response"):
                        messages.append(res["response"])
                    if res.get("speech"):
                        speeches.append(res["speech"])
                    time.sleep(0.5)

                combined_msg = " ".join(messages)
                combined_speech = " ".join(speeches)
                if self._on_response:
                    self._on_response(combined_msg, combined_speech)

                return {
                    "status": "ok",
                    "intent": "compound",
                    "response": combined_msg,
                    "speech": combined_speech,
                }

        return self._process_single_command(user_input)

    def _process_single_command(self, user_input: str) -> Dict[str, Any]:
        """Process a single atomic command string."""
        user_input = user_input.strip()
        if not user_input:
            return {"status": "empty", "speech": "I didn't catch that."}

        # 1. Store user message to memory
        self._memory.add_conversation_entry("user", user_input, self._session_id)

        # 2. Get recent history for AI context
        history = self._memory.get_conversation_history(limit=6, session_id=self._session_id)

        # 3. Parse intent via Ollama
        logger.info(f"Processing command: '{user_input}'")
        intent: IntentResponse = self._ai.parse_intent(user_input, history)
        logger.info(f"Intent resolved: action='{intent.action}', app='{intent.application}', value='{intent.value}'")

        # 4. Handle general chat separately (uses Gemini AI if available for intelligent free chat)
        if intent.action == "general_chat":
            if self._gemini.is_available():
                logger.info("Routing chat response through Gemini AI...")
                response_text = self._gemini.generate_chat_response(user_input, history)
            else:
                response_text = self._ai.generate_chat_response(user_input, history)
            speech_text = response_text
        else:
            # 5. Execute command via dispatcher
            result = self._dispatcher.dispatch(intent)
            response_text = result.get("message", "Done.")
            speech_text = result.get("speech") or intent.speech_response or response_text

            # Track app usage for frequently used app insight
            if intent.action == "open_application" and intent.application:
                self._memory.log_app_usage(intent.application)

        # 6. Store SARA's response to memory
        self._memory.add_conversation_entry("assistant", response_text, self._session_id)

        # 7. Fire GUI/Voice callback
        if self._on_response:
            self._on_response(response_text, speech_text)

        return {
            "status": "ok",
            "intent": intent.action,
            "response": response_text,
            "speech": speech_text,
        }

    def get_ai_status(self) -> Dict[str, Any]:
        """Return AI engine health check for status indicator."""
        return {
            "ollama_available": self._ai.is_available(),
            "gemini_available": self._gemini.is_available(),
            "model": self._ai._model,
            "registered_commands": len(self._dispatcher.list_registered()),
            "plugins": self._plugin_summary,
        }

    def get_plugins(self) -> List[Dict[str, Any]]:
        """Return list of all loaded plugin summaries for GUI display."""
        return self._plugin_summary

    def set_tts_engine(self, tts_engine) -> None:
        """Bind active TTS engine to voice commands."""
        if hasattr(self, '_switch_voice_cmd') and self._switch_voice_cmd:
            self._switch_voice_cmd.set_tts_engine(tts_engine)
        logger.info("Bound TTS engine to SARAEngine voice commands.")

    def process_command_direct(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action directly by name without AI intent parsing.
        Used by internal components (scheduler, routines) to fire commands.
        """
        from ai.schemas import IntentResponse
        intent = IntentResponse(action=action, params=params)
        result = self._dispatcher.dispatch(intent)
        logger.debug(f"Direct dispatch: {action} -> {result.get('status')}")
        return result
