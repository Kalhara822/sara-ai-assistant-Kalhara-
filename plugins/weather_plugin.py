"""
Weather Plugin for SARA AI Assistant
Fetches current weather data using Open-Meteo API (free, no API key required).
Demonstrates the SARA single-file plugin architecture.

To install: drop this file into the plugins/ folder. SARA auto-loads it.
"""

import urllib.request
import urllib.parse
import json
from typing import Dict, Any, List
from plugins.base import BasePlugin
from utils.logger import logger


class WeatherPlugin(BasePlugin):
    """
    Weather Plugin — fetches real-time weather from Open-Meteo (free, no key).
    Supports: check_weather action.
    Drop this file into plugins/ to auto-register.
    """

    # Default location: Colombo, Sri Lanka (overridable via preferences)
    DEFAULT_LAT = 6.9271
    DEFAULT_LON = 79.8612
    DEFAULT_CITY = "Colombo"

    # WMO Weather Code to description mapping
    WMO_CODES = {
        0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 48: "icy fog",
        51: "light drizzle", 53: "moderate drizzle", 55: "heavy drizzle",
        61: "light rain", 63: "moderate rain", 65: "heavy rain",
        71: "light snow", 73: "moderate snow", 75: "heavy snow",
        77: "snow grains", 80: "light showers", 81: "moderate showers",
        82: "violent showers", 85: "light snow showers", 86: "heavy snow showers",
        95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm",
    }

    @property
    def plugin_name(self) -> str:
        return "WeatherPlugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_actions(self) -> List[str]:
        return ["check_weather"]

    def initialize(self) -> bool:
        logger.info(f"[WeatherPlugin] Initialized (Open-Meteo, no API key required).")
        return True

    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "check_weather":
            return self._get_weather(params)
        return {"status": "error", "message": f"Unknown action: {action}"}

    def _get_weather(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch current weather conditions from Open-Meteo API."""
        lat = params.get("lat", self.DEFAULT_LAT)
        lon = params.get("lon", self.DEFAULT_LON)
        city = params.get("city", self.DEFAULT_CITY)

        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                f"&current_weather=true"
                f"&hourly=relative_humidity_2m"
                f"&timezone=auto"
            )
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode())

            weather = data.get("current_weather", {})
            temp_c = weather.get("temperature", "?")
            wind_kph = weather.get("windspeed", "?")
            code = weather.get("weathercode", 0)
            description = self.WMO_CODES.get(code, "unknown conditions")

            # Get humidity from first hourly reading
            humidity = "?"
            try:
                humidity = data["hourly"]["relative_humidity_2m"][0]
            except (KeyError, IndexError):
                pass

            msg = (
                f"Currently in {city}: {description}, "
                f"{temp_c}°C, wind {wind_kph} km/h, "
                f"humidity {humidity}%."
            )
            logger.info(f"[WeatherPlugin] {msg}")
            return {
                "status": "success",
                "message": msg,
                "data": {
                    "temperature_c": temp_c,
                    "wind_kph": wind_kph,
                    "description": description,
                    "humidity": humidity,
                    "city": city,
                }
            }

        except Exception as e:
            logger.error(f"[WeatherPlugin] Error fetching weather: {e}")
            return {
                "status": "error",
                "message": "Unable to fetch weather data. Please check your internet connection."
            }
