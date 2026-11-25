"""
Voice Orchestrator / Wake Word Listener
Manages full voice interaction loop:
  Wake Word → Listen → Transcribe → Return text to AI dispatcher
Runs continuously in a background thread without blocking the GUI.
"""

import threading
import time
from typing import Optional, Callable
from voice.stt_engine import WhisperSTTEngine
from voice.tts_engine import EdgeTTSEngine
from config import config
from utils.logger import logger


class VoiceOrchestrator:
    """
    Coordinates wake-word listening, speech recognition, and TTS response.
    All operations run in daemon threads so GUI remains fully responsive.
    """

    def __init__(
        self,
        on_command_received: Optional[Callable[[str], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
    ):
        self.stt = WhisperSTTEngine()
        self.tts = EdgeTTSEngine()

        self._on_command = on_command_received
        self._on_status = on_status_change
        self._on_audio_level = on_audio_level

        self._wake_word = config.voice.WAKE_WORD.lower()
        self._is_running = False
        self._is_listening_mode = False
        self._listen_thread: Optional[threading.Thread] = None
        self._wake_thread: Optional[threading.Thread] = None

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def start_wake_word_mode(self) -> None:
        """Begin continuous background wake word detection loop."""
        if self._is_running:
            return
        self._is_running = True
        self._wake_thread = threading.Thread(
            target=self._wake_word_loop,
            name="WakeWord-Listener",
            daemon=True
        )
        self._wake_thread.start()
        logger.info(f"Wake word listener started. Say '{self._wake_word}' to activate SARA.")

    def stop_wake_word_mode(self) -> None:
        """Stop wake word detection loop."""
        self._is_running = False
        logger.info("Wake word listener stopped.")

    def listen_once(self) -> None:
        """Single-shot listen triggered manually (e.g. by mic button)."""
        if self._is_listening_mode:
            return
        self._listen_thread = threading.Thread(
            target=self._do_listen_and_dispatch,
            name="Manual-Listen",
            daemon=True
        )
        self._listen_thread.start()

    def set_voice_profile(self, profile_key: str) -> bool:
        """Switch TTS voice profile: 'default', 'jarvis', or 'cute'."""
        return self.tts.set_profile(profile_key)

    def speak(self, text: str) -> None:
        """Speak a response using the active TTS voice profile."""
        def _on_start():
            self._set_status("SPEAKING")

        def _on_done():
            self._set_status("ONLINE")

        self.tts.speak(text, on_start=_on_start, on_complete=_on_done)

    def stop_speaking(self) -> None:
        """Interrupt current speech."""
        self.tts.stop()

    # -----------------------------------------------------------------------
    # Private Internals
    # -----------------------------------------------------------------------

    def _wake_word_loop(self) -> None:
        """Continuous loop: listen for wake word, then activate command mode."""
        self._set_status("ONLINE")
        while self._is_running:
            try:
                detected = self.stt.detect_wake_word(self._wake_word)
                if detected and self._is_running:
                    logger.info("Wake word detected — activating SARA.")
                    self._do_listen_and_dispatch()
            except Exception as e:
                logger.error(f"Wake word loop error: {e}", exc_info=True)
                time.sleep(1.0)

    def _do_listen_and_dispatch(self) -> None:
        """Full listen → transcribe → dispatch cycle."""
        self._is_listening_mode = True
        try:
            # Acknowledge activation
            self._set_status("LISTENING")
            text = self.stt.listen_and_transcribe(on_audio_level=self._on_audio_level)

            if text:
                logger.info(f"Voice command captured: '{text}'")
                self._set_status("THINKING")
                if self._on_command:
                    self._on_command(text)
            else:
                logger.info("No speech detected after wake word.")
                self._set_status("ONLINE")

        except Exception as e:
            logger.error(f"Listen dispatch error: {e}", exc_info=True)
            self._set_status("ONLINE")
        finally:
            self._is_listening_mode = False

    def _set_status(self, status: str) -> None:
        """Propagate status change to GUI callback."""
        if self._on_status:
            self._on_status(status)
