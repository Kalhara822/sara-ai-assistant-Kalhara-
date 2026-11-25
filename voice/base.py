"""
Abstract Base Classes for Voice Services (Speech-to-Text & Text-to-Speech)
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional

class BaseSTTEngine(ABC):
    """Abstract interface for Speech-To-Text engines (Whisper)."""

    @abstractmethod
    def listen_and_transcribe(self, on_audio_level: Optional[Callable[[float], None]] = None) -> Optional[str]:
        """Record audio input and return transcribed string."""
        pass

    @abstractmethod
    def detect_wake_word(self, keyword: str = "sara") -> bool:
        """Listen continuously for wake word activation."""
        pass


class BaseTTSEngine(ABC):
    """Abstract interface for Text-To-Speech engines (Edge TTS)."""

    @abstractmethod
    def speak(self, text: str, on_start: Optional[Callable[[], None]] = None, on_complete: Optional[Callable[[], None]] = None) -> None:
        """Synthesize and play spoken output (Using female neural voice)."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Interrupt active speech synthesis."""
        pass
