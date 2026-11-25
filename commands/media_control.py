"""
Media Control Commands
Handles: set_volume, increase_volume, decrease_volume, mute_volume,
         set_brightness, increase_brightness, decrease_brightness
"""

from typing import Dict, Any
from commands.base import BaseCommand
from utils.logger import logger

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    import ctypes
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False
    logger.warning("pycaw not available. Volume control disabled.")

try:
    import screen_brightness_control as sbc
    HAS_SBC = True
except Exception:
    HAS_SBC = False
    logger.warning("screen-brightness-control not available. Brightness control disabled.")


def _get_volume_interface():
    """Return pycaw volume interface for the default audio endpoint."""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
    except Exception:
        # Fallback for newer pycaw versions
        from pycaw.pycaw import AudioUtilities
        device = AudioUtilities.GetSpeakers()
        interface = device.EndpointVolume
        return interface


class SetVolumeCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "set_volume"

    @property
    def description(self) -> str:
        return "Set system master volume to a specific percentage (0-100)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_PYCAW:
            return {"status": "error", "message": "Volume control not available on this system."}
        try:
            level = max(0, min(100, int(params.get("value", 50))))
            vol = _get_volume_interface()
            vol.SetMasterVolumeLevelScalar(level / 100.0, None)
            logger.info(f"Volume set to {level}%")
            return {"status": "success", "message": f"Volume set to {level}%."}
        except Exception as e:
            logger.error(f"Set volume error: {e}")
            return {"status": "error", "message": str(e)}


class IncreaseVolumeCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "increase_volume"

    @property
    def description(self) -> str:
        return "Increase system volume by 10%."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_PYCAW:
            return {"status": "error", "message": "Volume control not available."}
        try:
            vol = _get_volume_interface()
            current = vol.GetMasterVolumeLevelScalar()
            new_level = min(1.0, current + 0.10)
            vol.SetMasterVolumeLevelScalar(new_level, None)
            return {"status": "success", "message": f"Volume increased to {int(new_level*100)}%."}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class DecreaseVolumeCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "decrease_volume"

    @property
    def description(self) -> str:
        return "Decrease system volume by 10%."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_PYCAW:
            return {"status": "error", "message": "Volume control not available."}
        try:
            vol = _get_volume_interface()
            current = vol.GetMasterVolumeLevelScalar()
            new_level = max(0.0, current - 0.10)
            vol.SetMasterVolumeLevelScalar(new_level, None)
            return {"status": "success", "message": f"Volume decreased to {int(new_level*100)}%."}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class MuteVolumeCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "mute_volume"

    @property
    def description(self) -> str:
        return "Toggle mute/unmute system audio."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_PYCAW:
            return {"status": "error", "message": "Volume control not available."}
        try:
            vol = _get_volume_interface()
            current_mute = vol.GetMute()
            vol.SetMute(not current_mute, None)
            state = "muted" if not current_mute else "unmuted"
            return {"status": "success", "message": f"Audio {state}."}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class SetBrightnessCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "set_brightness"

    @property
    def description(self) -> str:
        return "Set screen brightness to a specific level (0-100)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_SBC:
            return {"status": "error", "message": "Brightness control not available."}
        try:
            level = max(0, min(100, int(params.get("value", 75))))
            sbc.set_brightness(level)
            return {"status": "success", "message": f"Brightness set to {level}%."}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class IncreaseBrightnessCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "increase_brightness"

    @property
    def description(self) -> str:
        return "Increase screen brightness by 10%."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_SBC:
            return {"status": "error", "message": "Brightness control not available."}
        try:
            current = sbc.get_brightness()[0]
            new_level = min(100, current + 10)
            sbc.set_brightness(new_level)
            return {"status": "success", "message": f"Brightness increased to {new_level}%."}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class DecreaseBrightnessCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "decrease_brightness"

    @property
    def description(self) -> str:
        return "Decrease screen brightness by 10%."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_SBC:
            return {"status": "error", "message": "Brightness control not available."}
        try:
            current = sbc.get_brightness()[0]
            new_level = max(0, current - 10)
            sbc.set_brightness(new_level)
            return {"status": "success", "message": f"Brightness decreased to {new_level}%."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
