"""
Voice Profile Commands
SARA operates exclusively with her dedicated SARA Female Neural voice.
"""

from typing import Dict, Any
from commands.base import BaseCommand
from utils.logger import logger


class SwitchVoiceCommand(BaseCommand):
    def __init__(self, tts_engine=None):
        self._tts_engine = tts_engine

    def set_tts_engine(self, tts_engine) -> None:
        self._tts_engine = tts_engine

    @property
    def action_name(self) -> str:
        return "switch_voice"

    @property
    def description(self) -> str:
        return "Confirms SARA's dedicated female voice profile."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._tts_engine:
            self._tts_engine.set_profile("default")

        msg = "I operate exclusively with my dedicated SARA female voice profile."
        logger.info(f"SwitchVoiceCommand executed -> SARA Female Voice dedicated")
        return {
            "status": "success",
            "message": msg,
            "profile": "default"
        }
