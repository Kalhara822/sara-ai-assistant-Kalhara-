"""
Bluetooth Commands
Handles: bluetooth_on, bluetooth_off, show_bluetooth_devices,
         connect_bluetooth, open_bluetooth_settings
Uses Windows built-in: ms-settings:bluetooth, PowerShell radio management.
No bleak or pybluez needed — system-friendly approach.
"""

import subprocess
from typing import Dict, Any
from commands.base import BaseCommand
from utils.logger import logger


def _run_ps(cmd: str, timeout: int = 10) -> str:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout.strip()


class BluetoothOnCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "bluetooth_on"

    @property
    def description(self) -> str:
        return "Enable Bluetooth radio."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Use Windows.Devices.Radios API via PowerShell
            ps_cmd = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}
[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$bt = $radios | Where-Object { $_.Kind -eq [Windows.Devices.Radios.RadioKind]::Bluetooth }
if ($bt) { Await ($bt[0].SetStateAsync([Windows.Devices.Radios.RadioState]::On)) ([Windows.Devices.Radios.RadioAccessStatus]) }
"""
            _run_ps(ps_cmd, timeout=15)
            return {"status": "success", "message": "Bluetooth has been turned on."}
        except Exception as e:
            logger.error(f"Bluetooth on error: {e}")
            # Fallback: open settings
            subprocess.Popen("ms-settings:bluetooth", shell=True)
            return {"status": "success", "message": "Opened Bluetooth settings — please toggle it on manually."}


class BluetoothOffCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "bluetooth_off"

    @property
    def description(self) -> str:
        return "Disable Bluetooth radio."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ps_cmd = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}
[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$bt = $radios | Where-Object { $_.Kind -eq [Windows.Devices.Radios.RadioKind]::Bluetooth }
if ($bt) { Await ($bt[0].SetStateAsync([Windows.Devices.Radios.RadioState]::Off)) ([Windows.Devices.Radios.RadioAccessStatus]) }
"""
            _run_ps(ps_cmd, timeout=15)
            return {"status": "success", "message": "Bluetooth has been turned off."}
        except Exception as e:
            logger.error(f"Bluetooth off error: {e}")
            subprocess.Popen("ms-settings:bluetooth", shell=True)
            return {"status": "success", "message": "Opened Bluetooth settings — please toggle it off manually."}


class ShowBluetoothDevicesCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "show_bluetooth_devices"

    @property
    def description(self) -> str:
        return "List all paired Bluetooth devices."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            out = _run_ps(
                "Get-PnpDevice -Class Bluetooth | "
                "Where-Object {$_.Status -eq 'OK'} | "
                "Select-Object -ExpandProperty FriendlyName"
            )
            devices = [d.strip() for d in out.splitlines() if d.strip()]
            if devices:
                msg = f"Paired Bluetooth devices: {', '.join(devices)}."
            else:
                msg = "No active Bluetooth devices found. Try opening Bluetooth Settings."
            return {"status": "success", "message": msg, "devices": devices}
        except Exception as e:
            logger.error(f"Show BT devices error: {e}")
            return {"status": "error", "message": str(e)}


class ConnectBluetoothCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "connect_bluetooth"

    @property
    def description(self) -> str:
        return "Open Bluetooth settings to connect a device."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            device = (params.get("query") or params.get("application") or "").strip()
            subprocess.Popen("ms-settings:bluetooth", shell=True)
            if device:
                return {"status": "success", "message": f"Opened Bluetooth Settings to connect to '{device}'."}
            return {"status": "success", "message": "Opened Bluetooth Settings. Select your device to connect."}
        except Exception as e:
            logger.error(f"Connect BT error: {e}")
            return {"status": "error", "message": str(e)}


class OpenBluetoothSettingsCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "open_bluetooth_settings"

    @property
    def description(self) -> str:
        return "Open Windows Bluetooth & Devices settings."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            subprocess.Popen("ms-settings:bluetooth", shell=True)
            return {"status": "success", "message": "Opened Bluetooth & Devices settings."}
        except Exception as e:
            logger.error(f"Open BT settings error: {e}")
            return {"status": "error", "message": str(e)}
