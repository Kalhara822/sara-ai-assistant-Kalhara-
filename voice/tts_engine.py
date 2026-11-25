"""
Edge-TTS Female Neural Voice Engine
Text-to-Speech synthesis using Microsoft Azure Cognitive Services via edge-tts.
Default voice: en-US-AvaNeural (High-Quality Female Neural Voice)
"""

import asyncio
import threading
import tempfile
import os
from typing import Optional, Callable
from voice.base import BaseTTSEngine
from config import config
from utils.logger import logger

try:
    import edge_tts
    import sounddevice as sd
    import soundfile as sf
    HAS_EDGE_TTS = True
except ImportError as _e:
    HAS_EDGE_TTS = False
    logger.warning(f"TTS dependency missing ({_e}). Install: pip install edge-tts sounddevice soundfile")

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False
    logger.warning("pyttsx3 not installed. Offline TTS fallback unavailable.")


class EdgeTTSEngine(BaseTTSEngine):
    """
    Microsoft Edge Neural TTS Engine.
    Uses en-US-AvaNeural (female, premium quality) as default SARA voice.
    Runs synthesis in a background thread to avoid blocking the GUI.
    """

    # Exclusive Voice Profile: SARA Female
    VOICE_PROFILES = {
        "default": {
            "key": "default",
            "name": "SARA (Female)",
            "voice": "en-US-AvaNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
            "description": "Standard clear, intelligent, and focused SARA female voice"
        }
    }

    def __init__(self):
        self._current_profile_key = "default"
        profile = self.VOICE_PROFILES["default"]
        self._voice = profile["voice"]
        self._rate = profile["rate"]
        self._pitch = profile["pitch"]
        self._is_speaking = False
        self._stop_event = threading.Event()
        self._speak_thread: Optional[threading.Thread] = None
        logger.info(f"EdgeTTSEngine initialized with exclusive SARA female voice ({self._voice})")

    @property
    def current_voice(self) -> str:
        return self._voice

    @property
    def current_profile(self) -> str:
        return self._current_profile_key

    def set_profile(self, profile_key: str = "default") -> bool:
        """SARA operates exclusively with her dedicated female voice."""
        self._current_profile_key = "default"
        profile = self.VOICE_PROFILES["default"]
        self._voice = profile["voice"]
        self._rate = profile["rate"]
        self._pitch = profile["pitch"]
        logger.info(f"Using exclusive SARA female voice: {self._voice}")
        return True

    def set_voice(self, voice_key: str) -> bool:
        """Ensure voice remains SARA female voice."""
        return self.set_profile("default")

    def speak(
        self,
        text: str,
        on_start: Optional[Callable[[], None]] = None,
        on_complete: Optional[Callable[[], None]] = None
    ) -> None:
        """
        Speak text asynchronously in a background thread.
        Tries Edge TTS (online, high quality) first; falls back to pyttsx3 (offline) on failure.
        Calls on_start() before playback and on_complete() after.
        """
        if self._is_speaking:
            self.stop()

        self._stop_event.clear()

        def _run():
            self._is_speaking = True
            if on_start:
                on_start()
            spoken = False
            # --- Attempt 1: Edge TTS (online, premium quality) ---
            if HAS_EDGE_TTS:
                try:
                    asyncio.run(self._synthesize_and_play(text))
                    spoken = True
                except Exception as e:
                    logger.warning(f"Edge TTS failed (network issue?): {e}. Falling back to offline TTS.")
            # --- Attempt 2: pyttsx3 offline fallback ---
            if not spoken:
                if HAS_PYTTSX3:
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty("rate", 175)
                        # Try to pick a female voice
                        voices = engine.getProperty("voices")
                        for v in voices:
                            if "female" in v.name.lower() or "zira" in v.name.lower() or "hazel" in v.name.lower():
                                engine.setProperty("voice", v.id)
                                break
                        engine.say(text)
                        engine.runAndWait()
                        engine.stop()
                        spoken = True
                        logger.info("Spoke via pyttsx3 offline fallback.")
                    except Exception as e:
                        logger.error(f"pyttsx3 offline TTS also failed: {e}", exc_info=True)
                else:
                    logger.error("No TTS engine available (edge-tts offline, pyttsx3 not installed).")
            self._is_speaking = False
            if on_complete:
                on_complete()

        self._speak_thread = threading.Thread(target=_run, name="TTS-Worker", daemon=True)
        self._speak_thread.start()

    async def _synthesize_and_play(self, text: str) -> None:
        """Async: synthesize voice audio, write to temp file, play it back."""
        tmp_path = None
        try:
            communicate = edge_tts.Communicate(text, self._voice, rate=self._rate, pitch=self._pitch)

            # Write to a temporary mp3 file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            await communicate.save(tmp_path)

            if self._stop_event.is_set():
                return

            # Read audio and play via sounddevice
            data, samplerate = sf.read(tmp_path, dtype="float32")
            sd.play(data, samplerate)
            sd.wait()

        except Exception as e:
            logger.error(f"Edge TTS playback error: {e}", exc_info=True)
            raise
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    def stop(self) -> None:
        """Interrupt any active speech playback."""
        self._stop_event.set()
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        self._is_speaking = False
        logger.debug("TTS speech stopped.")

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking
