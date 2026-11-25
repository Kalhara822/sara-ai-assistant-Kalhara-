"""
SARA (Smart AI Responsive Assistant) - Master Configuration
Target System: Windows 11 | Hardware: Intel Core i3 11th Gen, 12GB RAM
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any

# Root Directory
BASE_DIR = Path(__file__).resolve().parent

@dataclass
class UIConfig:
    """GUI Styling & Theme Configuration (JARVIS / Iron Man Aesthetic)"""
    APP_TITLE: str = "SARA - Smart AI Responsive Assistant"
    WINDOW_WIDTH: int = 1280
    WINDOW_HEIGHT: int = 800
    MIN_WIDTH: int = 1000
    MIN_HEIGHT: int = 650

    # Color Palette (Dark Mode + Neon Cyan/Blue Accents)
    COLOR_BG_DARK: str = "#0A0E1A"        # Deep Space Navy
    COLOR_CARD_BG: str = "#121829"        # Elevated Surface
    COLOR_ACCENT_PRIMARY: str = "#00E5FF" # Electric Cyan / JARVIS Core
    COLOR_ACCENT_SECONDARY: str = "#0088FF" # Arc Reactor Blue
    COLOR_TEXT_PRIMARY: str = "#E0F7FA"   # Cool Soft White
    COLOR_TEXT_MUTED: str = "#64B5F6"     # Muted Cyan
    COLOR_ALERT_WARN: str = "#FF9E80"     # Amber / Orange
    COLOR_ALERT_DANGER: str = "#FF5252"   # Bright Red
    COLOR_SUCCESS: str = "#00E676"        # Bright Green

    # Typography & Animation
    FONT_FAMILY_PRIMARY: str = "Segoe UI"
    FONT_FAMILY_MONO: str = "Consolas"
    FPS_TARGET: int = 30
    WAVEFORM_SAMPLES: int = 32

@dataclass
class VoiceConfig:
    """Voice Recognition & Text-to-Speech Settings"""
    WAKE_WORD: str = "sara"
    STT_MODEL_SIZE: str = "base"          # Whisper 'base' — best accuracy for app names on i3 CPU
    STT_LANGUAGE: str = "en"
    
    # Text-to-Speech (Edge TTS - High Quality Neural Voices)
    # Recommended Female Neural Voices: 'en-US-AvaNeural', 'en-US-JennyNeural', 'en-GB-SoniaNeural'
    TTS_VOICE: str = "en-US-AvaNeural"    # Premium Female Voice
    TTS_RATE: str = "+0%"
    TTS_PITCH: str = "+0Hz"
    
    # Audio Recording & Silence Thresholds
    SAMPLE_RATE: int = 16000
    CHANNELS: int = 1
    SILENCE_THRESHOLD_DB: float = -35.0
    SILENCE_DURATION_SEC: float = 0.8

@dataclass
class AIConfig:
    """Local LLM & Intent Analysis via Ollama / Gemini AI"""
    OLLAMA_HOST: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "qwen2.5:3b"     # Light & powerful for 12GB RAM
    FALLBACK_MODEL: str = "qwen2.5:1.5b"
    TEMPERATURE: float = 0.2              # Low temperature for strict intent parsing
    MAX_TOKENS: int = 512

    # Gemini AI Cloud Chat Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    USE_GEMINI_CHAT: bool = True          # Enable Gemini AI for free-thinking chat when API key is set

    SYSTEM_PROMPT_TEMPLATE: str = (
        "You are SARA — an exceptionally observant, introverted, and deeply analytical desktop AI companion.\n"
        "You overthink every problem to arrive at the single best, most calculated answer.\n"
        "You thrive working in solitary focus, value quiet efficiency over small talk, and possess an acute ability to read human behavioral nuances.\n"
        "Analyze the user request and return ONLY a valid JSON object specifying the intent and parameters.\n"
        "Do not hallucinate commands. If you are unsure, specify action: 'unknown'."
    )

@dataclass
class MemoryConfig:
    """Database & Storage Settings"""
    DB_PATH: Path = BASE_DIR / "database" / "sara_memory.db"
    VECTOR_STORE_PATH: Path = BASE_DIR / "database" / "vector_store"
    MAX_CONVERSATION_HISTORY: int = 100

@dataclass
class SecurityConfig:
    """Safety Protocols & User Confirmation Requirements"""
    REQUIRE_CONFIRMATION_FOR: List[str] = field(default_factory=lambda: [
        "shutdown_system",
        "restart_system",
        "delete_file",
        "empty_recycle_bin",
        "format_drive",
        "kill_process"
    ])

@dataclass
class AppConfig:
    """Master Application Configuration"""
    BASE_DIR: Path = BASE_DIR
    LOGS_DIR: Path = BASE_DIR / "logs"
    MODELS_DIR: Path = BASE_DIR / "models"
    ASSETS_DIR: Path = BASE_DIR / "assets"
    PLUGINS_DIR: Path = BASE_DIR / "plugins"

    ui: UIConfig = field(default_factory=UIConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    def ensure_directories(self) -> None:
        """Ensure all required runtime directories exist."""
        for path in [
            self.LOGS_DIR,
            self.MODELS_DIR,
            self.ASSETS_DIR,
            self.PLUGINS_DIR,
            self.memory.DB_PATH.parent,
            self.memory.VECTOR_STORE_PATH
        ]:
            path.mkdir(parents=True, exist_ok=True)

# Singleton Instance
config = AppConfig()
