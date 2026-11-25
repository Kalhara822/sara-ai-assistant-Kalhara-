"""
OpenAI Whisper Speech-to-Text Engine
Local, offline transcription optimized for Intel i3 / 12GB RAM.
Uses 'tiny' model for wake word detection and 'base' model for command transcription.
Includes phonetic correction map for common mishearings (WhatsApp, YouTube, VS Code, etc.)
"""

import re
import threading
import queue
import numpy as np
from typing import Optional, Callable
from voice.base import BaseSTTEngine
from config import config
from utils.logger import logger

try:
    import whisper
    import sounddevice as sd
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    logger.warning("openai-whisper or sounddevice not installed. STT disabled.")


# ─────────────────────────────────────────────────────────────────────────────
# Phonetic Correction Map
# Fixes common Whisper tiny/base mishearings for app names and SARA commands.
# ─────────────────────────────────────────────────────────────────────────────
CORRECTIONS: dict = {
    # App Names
    "whatsup":          "whatsapp",
    "what's up":        "whatsapp",
    "what's app":       "whatsapp",
    "what sap":         "whatsapp",
    "whats up":         "whatsapp",
    "what app":         "whatsapp",
    "wassup":           "whatsapp",
    "what sup":         "whatsapp",
    "you tube":         "youtube",
    "u tube":           "youtube",
    "utube":            "youtube",
    "you too":          "youtube",
    "you tub":          "youtube",
    "crome":            "chrome",
    "grome":            "chrome",
    "crohn":            "chrome",
    "google crome":     "google chrome",
    "tele gram":        "telegram",
    "telegrams":        "telegram",
    "vs. code":         "vs code",
    "visco":            "vscode",
    "viscount":         "vscode",
    "vs cold":          "vs code",
    "vis code":         "vscode",
    "visual studio code": "vs code",
    "tele gram":        "telegram",
    "telegrams":        "telegram",
    "who's app":        "whatsapp",
    "spotify":          "spotify",
    "spot if i":        "spotify",
    "discord":          "discord",
    "disc cord":        "discord",
    "intellij":         "intellij",
    "intel ij":         "intellij",
    "intellect":        "intellij",
    "cap cut":          "capcut",
    "cap cod":          "capcut",
    "android studio":   "android studio",
    "calculator":       "calculator",
    "calculate":        "calculator",
    "calc later":       "calculator",
    "notepad":          "notepad",
    "note pad":         "notepad",
    "pot player":       "potplayer",
    "winrar":           "winrar",
    "win rar":          "winrar",
    # Commands
    "screenshot":       "screenshot",
    "screen shot":      "screenshot",
    "screen shirt":     "screenshot",
    "screen chat":      "screenshot",
    "lock pc":          "lock pc",
    "lock the pc":      "lock pc",
    "lock my pc":       "lock my pc",
    "shutdown":         "shutdown",
    "shut down":        "shutdown",
    "shut don":         "shutdown",
    "trimmer emory":    "trim memory",
    "trim memory":      "trim memory",
    "trimmemory":       "trim memory",
    "try memory":       "trim memory",
    "trend memory":     "trim memory",
    "system health":    "system health",
    "system help":      "system health",
    "health check":     "health check",
    "check weather":    "check weather",
    "what's the weather": "check weather",
    "weather":          "weather",
    "increase volume":  "increase volume",
    "volume up":        "increase volume",
    "decrease volume":  "decrease volume",
    "volume down":      "decrease volume",
    "mute":             "mute",
    "cpu usage":        "cpu usage",
    "see p usage":      "cpu usage",
    "ram usage":        "ram usage",
    "memory usage":     "ram usage",
    "github":           "github",
    "git hub":          "github",
    "git have":         "github",
    "gmail":            "gmail",
    "g mail":           "gmail",
    "reddit":           "reddit",
    "red it":           "reddit",
    "chat gpt":         "chatgpt",
    "sharp gpt":        "chatgpt",
    "cat gpt":          "chatgpt",
    "organize":         "organise",
    "organise":         "organise",
    "downloads":        "downloads",
    "routines":         "routine",
    "morning routine":  "morning routine",
    "work mode":        "work mode",
    "night mode":       "night mode",
}

# Initial prompt to bias Whisper toward PC assistant commands
WHISPER_INITIAL_PROMPT = (
    "Open WhatsApp, open Chrome, go to YouTube, search YouTube for, "
    "take a screenshot, lock my PC, set volume to, increase volume, "
    "trim memory, check weather, open VS Code, open Telegram, organise downloads"
)


def _apply_corrections(text: str) -> str:
    """Apply phonetic corrections to raw Whisper transcription."""
    corrected = text.lower().strip()

    # Remove filler words and wake-word prefix at start
    corrected = re.sub(r"^(um|uh|hmm|hey|okay|ok)[,\s]+", "", corrected)
    corrected = re.sub(r"^(sara|hey sara)[,\s]+", "", corrected)
    corrected = corrected.strip()

    # Apply longer phrases first to avoid partial collisions
    sorted_corrections = sorted(CORRECTIONS.items(), key=lambda x: -len(x[0]))
    for wrong, right in sorted_corrections:
        corrected = re.sub(r"\b" + re.escape(wrong) + r"\b", right, corrected, flags=re.IGNORECASE)

    logger.debug(f"STT correction: '{text}' -> '{corrected}'")
    return corrected.strip()


class WhisperSTTEngine(BaseSTTEngine):
    """
    Local Whisper Speech-To-Text Engine.
    Optimized for Intel i3 / 12GB RAM using the 'base' model on CPU.
    Runs audio capture and transcription in background threads.
    """

    def __init__(self):
        self._model = None
        self._sample_rate = config.voice.SAMPLE_RATE
        self._channels = config.voice.CHANNELS
        self._silence_dur = config.voice.SILENCE_DURATION_SEC
        self._is_loaded = False
        self._loading_lock = threading.Lock()
        logger.info("WhisperSTTEngine created. Model will load on first use.")

    def _ensure_model_loaded(self) -> bool:
        """Lazy-load Whisper model on first transcription request."""
        if self._is_loaded:
            return True
        if not HAS_WHISPER:
            return False
        with self._loading_lock:
            if self._is_loaded:
                return True
            try:
                model_size = config.voice.STT_MODEL_SIZE
                logger.info(f"Loading Whisper '{model_size}' model (first run may take ~30s)...")
                self._model = whisper.load_model(model_size, download_root=str(config.MODELS_DIR))
                self._is_loaded = True
                logger.info(f"Whisper '{model_size}' model loaded successfully.")
                return True
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}", exc_info=True)
                return False

    def listen_and_transcribe(
        self,
        on_audio_level: Optional[Callable[[float], None]] = None
    ) -> Optional[str]:
        """
        Record from microphone until silence is detected, then transcribe.
        Returns transcribed string or None if failed.
        """
        if not self._ensure_model_loaded():
            logger.error("Whisper model not available for transcription.")
            return None

        try:
            logger.info("STT: Listening for speech...")
            audio_frames = []
            silence_frames = 0
            silence_threshold = 0.01  # RMS amplitude threshold
            silence_limit = int(self._silence_dur * self._sample_rate / 512)

            def audio_callback(indata, frames, time_info, status):
                audio_frames.append(indata.copy())
                rms = float(np.sqrt(np.mean(indata ** 2)))
                if on_audio_level:
                    on_audio_level(rms)

            with sd.InputStream(
                samplerate=self._sample_rate,
                channels=self._channels,
                dtype="float32",
                blocksize=512,
                callback=audio_callback
            ):
                # Record until prolonged silence
                recorded_chunks = 0
                while True:
                    sd.sleep(50)
                    recorded_chunks += 1

                    # Allow minimum 0.5s of recording
                    if recorded_chunks < 10:
                        continue

                    if len(audio_frames) > 0:
                        recent = audio_frames[-1]
                        rms = float(np.sqrt(np.mean(recent ** 2)))
                        if rms < silence_threshold:
                            silence_frames += 1
                        else:
                            silence_frames = 0

                        if silence_frames >= silence_limit:
                            break

                        # Safety max recording: 15 seconds
                        if recorded_chunks > 300:
                            break

            if not audio_frames:
                return None

            # Concatenate and transcribe
            audio_data = np.concatenate(audio_frames, axis=0).flatten()
            duration = len(audio_data) / self._sample_rate
            logger.info(f"STT: Transcribing {duration:.1f}s of audio...")

            result = self._model.transcribe(
                audio_data,
                language=config.voice.STT_LANGUAGE,
                fp16=False,                        # CPU inference only for i3
                initial_prompt=WHISPER_INITIAL_PROMPT,  # Bias toward SARA commands
                temperature=0.0,                   # Greedy decoding — most deterministic
                best_of=1,
            )
            raw_text = result.get("text", "").strip()
            logger.info(f"STT Raw Transcription: '{raw_text}'")

            # Apply phonetic correction map
            corrected = _apply_corrections(raw_text)
            if corrected != raw_text.lower().strip():
                logger.info(f"STT Corrected: '{raw_text}' -> '{corrected}'")
            else:
                logger.info(f"STT Transcription: '{corrected}'")

            return corrected if corrected else None

        except Exception as e:
            logger.error(f"STT error: {e}", exc_info=True)
            return None

    def detect_wake_word(self, keyword: str = "sara") -> bool:
        """
        Listen briefly (3-4s window) and check if wake word appears in transcription.
        Returns True if wake word detected.
        """
        if not self._ensure_model_loaded():
            return False
        try:
            audio_frames = []
            with sd.InputStream(
                samplerate=self._sample_rate,
                channels=self._channels,
                dtype="float32",
                blocksize=512,
                callback=lambda indata, f, t, s: audio_frames.append(indata.copy())
            ):
                sd.sleep(3000)  # 3-second listen window

            if not audio_frames:
                return False

            audio_data = np.concatenate(audio_frames, axis=0).flatten()
            result = self._model.transcribe(
                audio_data,
                language="en",
                fp16=False,
                initial_prompt="Sara, hey Sara",
                temperature=0.0
            )
            text = result.get("text", "").lower().strip()
            # Apply basic correction for wake word
            text = _apply_corrections(text)

            detected = keyword.lower() in text
            if detected:
                logger.info(f"Wake word '{keyword}' detected in: '{text}'")
            return detected

        except Exception as e:
            logger.error(f"Wake word detection error: {e}", exc_info=True)
            return False
