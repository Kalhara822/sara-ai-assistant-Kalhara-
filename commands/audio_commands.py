"""
Audio Commands — Extended
Handles: get_volume_level, change_audio_output,
         increase_mic_volume, decrease_mic_volume, mute_microphone, unmute_microphone
Uses pycaw (already a dependency) for audio endpoint control.
Falls back to nircmd-less PowerShell where pycaw isn't available.
"""

import subprocess
from typing import Dict, Any
from commands.base import BaseCommand
from utils.logger import logger

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, EDataFlow, ERole
    from comtypes import CLSCTX_ALL
    import ctypes
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False


def _get_volume_interface():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))


def _get_mic_interface():
    """Get the default microphone capture endpoint volume interface."""
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    devices = AudioUtilities.GetMicrophone()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))


class GetVolumeLevelCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "get_volume_level"

    @property
    def description(self) -> str:
        return "Report the current system master volume level as a percentage."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_PYCAW:
            # Fallback: use PowerShell
            try:
                ps = "(Get-AudioDevice -Playback).Volume"
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "[Math]::Round([Audio]::Volume * 100)"],
                    capture_output=True, text=True, timeout=5
                )
                level = result.stdout.strip()
                return {"status": "success", "message": f"Current volume is {level} percent."}
            except Exception:
                return {"status": "error", "message": "Volume control not available on this system."}
        try:
            vol = _get_volume_interface()
            level = int(vol.GetMasterVolumeLevelScalar() * 100)
            muted = vol.GetMute()
            state = " (muted)" if muted else ""
            return {"status": "success", "message": f"Volume is at {level}%{state}.", "value": level}
        except Exception as e:
            logger.error(f"Get volume error: {e}")
            return {"status": "error", "message": str(e)}


class ChangeAudioOutputCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "change_audio_output"

    @property
    def description(self) -> str:
        return "Open Windows Sound settings to switch the audio output device."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Open the Sound settings page — user can select device from there
            subprocess.Popen("ms-settings:sound", shell=True)
            return {"status": "success", "message": "Opened Sound settings. You can switch audio output devices there."}
        except Exception as e:
            logger.error(f"Change audio output error: {e}")
            return {"status": "error", "message": str(e)}


class IncreaseMicVolumeCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "increase_mic_volume"

    @property
    def description(self) -> str:
        return "Increase microphone input volume by 10%."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_PYCAW:
            return {"status": "error", "message": "Microphone control requires pycaw."}
        try:
            mic = _get_mic_interface()
            current = mic.GetMasterVolumeLevelScalar()
            new_level = min(1.0, current + 0.10)
            mic.SetMasterVolumeLevelScalar(new_level, None)
            return {"status": "success", "message": f"Microphone volume increased to {int(new_level*100)}%."}
        except Exception as e:
            logger.error(f"Increase mic volume error: {e}")
            return {"status": "error", "message": str(e)}


class DecreaseMicVolumeCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "decrease_mic_volume"

    @property
    def description(self) -> str:
        return "Decrease microphone input volume by 10%."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_PYCAW:
            return {"status": "error", "message": "Microphone control requires pycaw."}
        try:
            mic = _get_mic_interface()
            current = mic.GetMasterVolumeLevelScalar()
            new_level = max(0.0, current - 0.10)
            mic.SetMasterVolumeLevelScalar(new_level, None)
            return {"status": "success", "message": f"Microphone volume decreased to {int(new_level*100)}%."}
        except Exception as e:
            logger.error(f"Decrease mic volume error: {e}")
            return {"status": "error", "message": str(e)}


class MuteMicrophoneCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "mute_microphone"

    @property
    def description(self) -> str:
        return "Toggle microphone mute/unmute."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_PYCAW:
            return {"status": "error", "message": "Microphone control requires pycaw."}
        try:
            mic = _get_mic_interface()
            current = mic.GetMute()
            mic.SetMute(not current, None)
            state = "muted" if not current else "unmuted"
            return {"status": "success", "message": f"Microphone {state}."}
        except Exception as e:
            logger.error(f"Mute mic error: {e}")
            return {"status": "error", "message": str(e)}


class UnmuteMicrophoneCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "unmute_microphone"

    @property
    def description(self) -> str:
        return "Unmute the microphone."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_PYCAW:
            return {"status": "error", "message": "Microphone control requires pycaw."}
        try:
            mic = _get_mic_interface()
            mic.SetMute(0, None)
            return {"status": "success", "message": "Microphone unmuted."}
        except Exception as e:
            logger.error(f"Unmute mic error: {e}")
            return {"status": "error", "message": str(e)}


class UnmuteVolumeCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "unmute_volume"

    @property
    def description(self) -> str:
        return "Unmute system audio."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not HAS_PYCAW:
            return {"status": "error", "message": "Volume control not available."}
        try:
            vol = _get_volume_interface()
            vol.SetMute(0, None)
            return {"status": "success", "message": "Audio unmuted."}
        except Exception as e:
            logger.error(f"Unmute volume error: {e}")
            return {"status": "error", "message": str(e)}
