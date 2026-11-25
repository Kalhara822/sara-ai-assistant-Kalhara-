"""
Network Commands
Handles: wifi_on, wifi_off, show_wifi_networks, connect_wifi, disconnect_wifi,
         check_internet, show_ip_address, show_mac_address,
         test_network_speed, open_network_settings
All implemented using Windows built-in tools: netsh, ipconfig, ping — no new packages.
"""

import subprocess
import socket
import uuid
import re
from typing import Dict, Any
from commands.base import BaseCommand
from utils.logger import logger


def _run(cmd: str, timeout: int = 10) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)


def _run_ps(cmd: str, timeout: int = 10) -> str:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout.strip()


class WiFiOnCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "wifi_on"

    @property
    def description(self) -> str:
        return "Enable the Wi-Fi adapter."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = _run('netsh interface set interface "Wi-Fi" enable')
            if result.returncode == 0:
                return {"status": "success", "message": "Wi-Fi has been turned on."}
            # Try alternate adapter name
            _run('netsh interface set interface "WiFi" enable')
            return {"status": "success", "message": "Wi-Fi turned on."}
        except Exception as e:
            logger.error(f"WiFi on error: {e}")
            return {"status": "error", "message": str(e)}


class WiFiOffCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "wifi_off"

    @property
    def description(self) -> str:
        return "Disable the Wi-Fi adapter."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            _run('netsh interface set interface "Wi-Fi" disable')
            return {"status": "success", "message": "Wi-Fi has been turned off."}
        except Exception as e:
            logger.error(f"WiFi off error: {e}")
            return {"status": "error", "message": str(e)}


class ShowWifiNetworksCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "show_wifi_networks"

    @property
    def description(self) -> str:
        return "List all available Wi-Fi networks in range."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = _run("netsh wlan show networks mode=bssid")
            output = result.stdout
            # Extract SSID names
            ssids = re.findall(r"SSID\s+\d+\s+:\s+(.+)", output)
            ssids = [s.strip() for s in ssids if s.strip()]
            if ssids:
                msg = f"Found {len(ssids)} networks: {', '.join(ssids[:10])}."
            else:
                msg = "No Wi-Fi networks found. Make sure Wi-Fi is enabled."
            return {"status": "success", "message": msg, "networks": ssids}
        except Exception as e:
            logger.error(f"Show wifi networks error: {e}")
            return {"status": "error", "message": str(e)}


class ConnectWifiCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "connect_wifi"

    @property
    def description(self) -> str:
        return "Connect to a saved Wi-Fi network by SSID name."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ssid = (params.get("query") or params.get("application") or "").strip()
            if not ssid:
                return {"status": "error", "message": "Please specify a Wi-Fi network name to connect to."}
            result = _run(f'netsh wlan connect name="{ssid}"')
            if result.returncode == 0:
                return {"status": "success", "message": f"Connecting to Wi-Fi network '{ssid}'."}
            return {"status": "error", "message": f"Could not connect to '{ssid}'. Make sure it's a saved profile."}
        except Exception as e:
            logger.error(f"Connect wifi error: {e}")
            return {"status": "error", "message": str(e)}


class DisconnectWifiCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "disconnect_wifi"

    @property
    def description(self) -> str:
        return "Disconnect from the current Wi-Fi network."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            _run("netsh wlan disconnect")
            return {"status": "success", "message": "Disconnected from Wi-Fi."}
        except Exception as e:
            logger.error(f"Disconnect wifi error: {e}")
            return {"status": "error", "message": str(e)}


class CheckInternetCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "check_internet"

    @property
    def description(self) -> str:
        return "Check if the PC has an active internet connection."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=4)
            return {"status": "success", "message": "Internet connection is active. You're online!"}
        except OSError:
            return {"status": "success", "message": "No internet connection detected. You appear to be offline."}


class ShowIPAddressCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "show_ip_address"

    @property
    def description(self) -> str:
        return "Show the local and public IP address."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            # Try to get public IP via a quick DNS lookup approach
            try:
                public_ip = _run_ps(
                    "(Invoke-WebRequest -Uri 'https://api.ipify.org' -UseBasicParsing -TimeoutSec 4).Content"
                )
            except Exception:
                public_ip = "unavailable"
            msg = f"Local IP: {local_ip}"
            if public_ip and public_ip != "unavailable":
                msg += f" | Public IP: {public_ip}"
            return {"status": "success", "message": msg, "local_ip": local_ip}
        except Exception as e:
            logger.error(f"Show IP error: {e}")
            return {"status": "error", "message": str(e)}


class ShowMACAddressCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "show_mac_address"

    @property
    def description(self) -> str:
        return "Show the MAC address of the primary network adapter."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            mac_int = uuid.getnode()
            mac_str = ':'.join(f'{(mac_int >> (8 * i)) & 0xFF:02x}' for i in reversed(range(6)))
            return {"status": "success", "message": f"MAC address: {mac_str.upper()}", "mac": mac_str.upper()}
        except Exception as e:
            logger.error(f"Show MAC error: {e}")
            return {"status": "error", "message": str(e)}


class TestNetworkSpeedCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "test_network_speed"

    @property
    def description(self) -> str:
        return "Open a speed test website in the browser."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import webbrowser
            webbrowser.open("https://fast.com")
            return {"status": "success", "message": "Opening Fast.com speed test in your browser."}
        except Exception as e:
            logger.error(f"Speed test error: {e}")
            return {"status": "error", "message": str(e)}


class OpenNetworkSettingsCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "open_network_settings"

    @property
    def description(self) -> str:
        return "Open Windows Network & Internet Settings."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            subprocess.Popen("ms-settings:network", shell=True)
            return {"status": "success", "message": "Opened Network & Internet Settings."}
        except Exception as e:
            logger.error(f"Open network settings error: {e}")
            return {"status": "error", "message": str(e)}
