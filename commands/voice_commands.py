"""
Voice Profile Commands
Handles switching between the 3 voice profiles:
- 'default': SARA Standard Female Neural
- 'jarvis': British Male Tech AI
- 'cute': Soft & Upbeat Cute Female
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
        return "Switch SARA's voice profile to 'jarvis', 'cute', or 'default'."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        target = str(params.get("query") or params.get("application") or params.get("value") or "").lower().strip()

        if "jarvis" in target:
            profile_key = "jarvis"
        elif "cute" in target or "anime" in target:
            profile_key = "cute"
        elif "default" in target or "sara" in target or "normal" in target or "reset" in target:
            profile_key = "default"
        else:
            profile_key = target

        if self._tts_engine:
            success = self._tts_engine.set_profile(profile_key)
            if not success:
                return {
                    "status": "error",
                    "message": f"Could not switch to voice profile '{target}'. Available: 'jarvis', 'cute', or 'default'."
                }

        responses = {
            "jarvis": "JARVIS voice protocol activated, sir. Systems operational.",
            "cute": "Cute voice profile activated! I'm ready to help you!",
            "default": "Switched back to standard SARA voice profile."
        }

        msg = responses.get(profile_key, f"Voice profile changed to {profile_key}.")
        logger.info(f"SwitchVoiceCommand executed -> profile: {profile_key}")
        return {
            "status": "success",
            "message": msg,
            "profile": profile_key
        }
