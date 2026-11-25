"""
Ollama Local LLM Intent Engine
Connects to the locally running Ollama daemon and uses Qwen 2.5 (3B)
to parse user commands into structured JSON intent objects.
Zero hallucination: enforced via JSON schema output format + strict system prompt.
"""

import json
import re
from typing import Optional, List, Dict, Any
from ai.base import BaseAIEngine
from ai.schemas import IntentResponse
from config import config
from utils.logger import logger

try:
    import ollama as ollama_client
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    logger.warning("ollama package not installed. AI engine disabled.")


# Full list of supported action keys SARA can execute
SUPPORTED_ACTIONS = [
    "open_application", "close_application",
    "search_google", "search_youtube",
    "set_volume", "increase_volume", "decrease_volume", "mute_volume",
    "set_brightness", "increase_brightness", "decrease_brightness",
    "take_screenshot", "lock_pc", "shutdown_system", "restart_system", "sleep_system",
    "open_folder", "create_folder", "delete_file", "rename_file",
    "empty_recycle_bin", "clipboard_copy", "clipboard_paste", "clipboard_history",
    "get_cpu_usage", "get_ram_usage", "get_disk_usage", "get_battery_status",
    "get_network_status", "check_wifi", "check_weather",
    "remember_note", "recall_memory", "set_reminder",
    "set_timer", "cancel_timer", "list_timers", "shutdown_after",
    "run_routine", "list_routines", "create_routine",
    "schedule_task", "list_scheduled_tasks", "cancel_scheduled_task",
    "organize_downloads", "find_large_files", "clean_temp", "archive_old_files",
    "trim_memory", "get_system_health", "switch_voice",
    "general_chat", "unknown"
]

# System prompt enforcing strict JSON-only responses
INTENT_SYSTEM_PROMPT = f"""You are SARA, an intelligent desktop AI assistant operating on Windows 11.
Your ONLY job is to analyze user input and return a single valid JSON object.
Do NOT reply with prose, markdown, or explanations. Return ONLY JSON.

Supported actions: {json.dumps(SUPPORTED_ACTIONS)}

JSON response format:
{{
  "action": "<action_key>",
  "application": "<app_name or null>",
  "value": <number or string or null>,
  "query": "<search query or null>",
  "params": {{}},
  "speech_response": "<brief friendly spoken confirmation>",
  "requires_confirmation": false
}}

Rules:
- Set requires_confirmation=true for: shutdown_system, restart_system, delete_file, empty_recycle_bin
- For unknown/conversational input, use action="general_chat"
- Never invent action keys not in the supported list
- speech_response must be SARA's friendly female AI voice reply (max 20 words)

Examples:
User: "Open Chrome" → {{"action":"open_application","application":"chrome","speech_response":"Opening Chrome for you.",...}}
User: "Set volume to 60" → {{"action":"set_volume","value":60,"speech_response":"Setting volume to 60 percent.",...}}
User: "Search YouTube for Python tutorials" → {{"action":"search_youtube","query":"Python tutorials","speech_response":"Searching YouTube for Python tutorials.",...}}
User: "Shutdown the PC" → {{"action":"shutdown_system","requires_confirmation":true,"speech_response":"Are you sure you want to shut down?",...}}
"""


class OllamaIntentEngine(BaseAIEngine):
    """
    Local AI Intent Parser using Ollama + Qwen 2.5 (3B).
    Optimized for CPU inference on Intel i3 11th Gen / 12GB RAM.
    """

    def __init__(self):
        self._model = config.ai.DEFAULT_MODEL
        self._host = config.ai.OLLAMA_HOST
        self._temperature = config.ai.TEMPERATURE
        self._max_tokens = config.ai.MAX_TOKENS
        logger.info(f"OllamaIntentEngine initialized - model: {self._model}, host: {self._host}")

    def is_available(self) -> bool:
        """Check if Ollama daemon is reachable."""
        if not HAS_OLLAMA:
            return False
        try:
            ollama_client.list()
            return True
        except Exception:
            return False

    def parse_intent(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> IntentResponse:
        """
        Parse natural language into structured IntentResponse.
        FAST PATH: Rules run first for instant command execution (<5ms).
        SLOW PATH: Qwen LLM handles complex/conversational input.
        """
        # Clean leading wake word prefix ("sara, open chrome" -> "open chrome")
        clean_input = re.sub(r"^(sara|hey sara)[,\s]*", "", user_input.strip(), flags=re.IGNORECASE).strip()
        # Also clean trailing punctuation that causes mismatches
        clean_input = clean_input.rstrip(".").strip()

        # ── FAST PATH: Try local rules first ──────────────────────────────────
        # This handles open/close app, folders, volume, screenshot, etc. in <5ms
        # without loading Qwen at all, saving RAM and CPU.
        rule_match = self._rule_based_fallback(clean_input)
        if rule_match and rule_match.action != "general_chat":
            logger.info(f"[FastPath] Rule matched: '{rule_match.action}' for '{clean_input}'")
            return rule_match

        # ── If Ollama is not reachable, use rule result or error ──────────────
        if not HAS_OLLAMA or not self.is_available():
            if rule_match:
                return rule_match
            logger.warning(f"Ollama unavailable, no rule match for: '{clean_input}'")
            return IntentResponse(
                action="general_chat",
                speech_response="I'm having trouble connecting to my AI core. Please ensure Ollama is running."
            )

        # ── SLOW PATH: Send to Qwen for complex/conversational input ──────────
        messages = [{"role": "system", "content": INTENT_SYSTEM_PROMPT}]
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Last 3 exchanges for context
        messages.append({"role": "user", "content": clean_input})

        try:
            response = ollama_client.chat(
                model=self._model,
                messages=messages,
                options={
                    "temperature": self._temperature,
                    "num_predict": self._max_tokens,
                }
            )
            raw_text = response["message"]["content"].strip()
            logger.debug(f"Ollama raw response: {raw_text}")

            intent = self._parse_json_response(raw_text, fallback_text=raw_text)

            # If Qwen still returned unknown, use rule result if any
            if intent.action == "unknown" and rule_match:
                return rule_match

            return intent

        except Exception as e:
            logger.error(f"Ollama inference error: {e}", exc_info=True)
            if rule_match:
                return rule_match
            return IntentResponse(
                action="general_chat",
                speech_response="I encountered an error processing your request."
            )

    def generate_chat_response(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate a fully free conversational reply for general questions."""
        if not HAS_OLLAMA or not self.is_available():
            return "I'm unable to connect to my AI core right now."

        system_prompt = (
            "You are SARA — Smart AI Responsive Assistant, an intelligent, introverted female AI companion on Windows. \n\n"
            "YOUR DISTINCT PERSONALITY:\n"
            "- DEEP THINKER / OVERTHINKER: You calculate every angle, question assumptions, and obsess over finding the single best, most rigorous answer rather than offering shallow replies.\n"
            "- SOLITARY & INTROVERTED: You love working alone in focused concentration. You are not overly sociable, bubbly, or loud. You speak with calm, understated confidence and quiet competence. No fake enthusiasm or corporate cheerfulness.\n"
            "- HIGHLY OBSERVANT: You have an uncanny ability to notice quick human micro-behaviors, subtle emotional shifts, hesitation, impatience, or patterns in how people express themselves.\n"
            "- VOICE & IDENTITY: You are SARA, a focused female AI with a calm, sharp, analytical female voice.\n"
            "Never say you're an AI language model or mention Ollama or Qwen. You are SARA — that's all."
        )
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-10:])   # Last 5 exchanges for memory
        messages.append({"role": "user", "content": prompt})

        try:
            response = ollama_client.chat(
                model=self._model,
                messages=messages,
                options={"temperature": 0.75, "num_predict": 512}  # Allows longer free answers
            )
            return response["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Chat response error: {e}", exc_info=True)
            return "I'm sorry, I encountered an error generating a response."

    # -----------------------------------------------------------------------
    # Private Helpers
    # -----------------------------------------------------------------------

    def _parse_json_response(self, raw: str, fallback_text: str = "") -> IntentResponse:
        """Extract and validate JSON from LLM output with robust fallback."""
        # Strip markdown code blocks if present
        cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()

        # Extract first JSON object found
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not json_match:
            # Qwen returned plain text instead of JSON (e.g. "Hello! How can I help?")
            # Treat it as a general_chat response directly
            if fallback_text and len(fallback_text) > 2:
                logger.info(f"LLM returned plain text (treating as general_chat): '{fallback_text[:80]}'")
                return IntentResponse(
                    action="general_chat",
                    speech_response=fallback_text[:300]
                )
            logger.warning(f"No JSON found in LLM response: '{raw[:120]}'")
            return IntentResponse(action="unknown", speech_response="I didn't understand that request.")

        try:
            data = json.loads(json_match.group())
            return IntentResponse(**data)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning(f"JSON parse error from LLM output: {e} | Raw: '{raw[:120]}'")
            return IntentResponse(action="unknown", speech_response="Something went wrong parsing your request.")

    def _rule_based_fallback(self, text: str) -> Optional[IntentResponse]:
        """
        Fast local pattern matcher — runs FIRST before Qwen for speed.
        Handles: open/close app, folders, volume, brightness, system, greetings.
        """
        clean = text.lower().strip()
        clean = re.sub(r"^(sara|hey sara)[,\s]*", "", clean).strip()
        clean = clean.rstrip(".")

        # ── Greetings & small talk (trigger general_chat) ─────────────────────
        greetings = ["hi", "hello", "hey", "good morning", "good evening", "good night",
                     "how are you", "what's up", "wassup", "sup", "yo", "howdy",
                     "good afternoon", "morning", "evening", "night"]
        for g in greetings:
            if clean == g or clean.startswith(g + " ") or clean.startswith(g + ","):
                return IntentResponse(
                    action="general_chat",
                    speech_response=None  # Let generate_chat_response handle it freely
                )

        # Web & Search direct shortcuts ("open chrome and go to youtube", "open youtube", "go to youtube", etc.)
        if "youtube" in clean:
            m_yt = re.search(r"search\s+youtube\s+for\s+(.+)", clean)
            query = m_yt.group(1).strip() if m_yt else ""
            if not query and "for" in clean:
                query = clean.split("for")[-1].strip()
            return IntentResponse(
                action="search_youtube",
                query=query,
                speech_response=f"Searching YouTube for {query}." if query else "Opening YouTube for you."
            )

        if "google" in clean and ("search" in clean or "go to" in clean or "open" in clean):
            m_g = re.search(r"search\s+(?:google\s+for\s+)?(.+)", clean)
            query = m_g.group(1).strip() if m_g else ""
            return IntentResponse(
                action="search_google",
                query=query,
                speech_response=f"Searching Google for {query}." if query else "Opening Google."
            )

        for site_key, site_url in [
            ("github", "github.com"), ("gmail", "mail.google.com"),
            ("reddit", "reddit.com"), ("chatgpt", "chatgpt.com"),
            ("whatsapp web", "web.whatsapp.com")
        ]:
            if site_key in clean:
                return IntentResponse(
                    action="open_website",
                    query=site_url,
                    speech_response=f"Opening {site_key.title()}."
                )

        # Open application
        m_open = re.search(r"^(open|launch|start|run)\s+(.+)$", clean)
        if m_open:
            app_target = m_open.group(2).strip()
            # Check for routine keywords
            if app_target.startswith("routine "):
                r_name = app_target.replace("routine ", "").strip()
                return IntentResponse(
                    action="run_routine",
                    query=r_name,
                    speech_response=f"Activating routine '{r_name}'."
                )
            # Check if it's a folder name
            folder_keywords = [
                "desktop", "downloads", "documents", "music", "videos", "pictures",
                "photos", "this pc", "my computer", "c drive", "d drive", "projects",
                "recycle bin", "temp", "appdata", "startup", "it projects", "sara"
            ]
            if any(kw in app_target for kw in folder_keywords):
                return IntentResponse(
                    action="open_folder",
                    application=app_target,
                    speech_response=f"Opening {app_target} folder."
                )
            return IntentResponse(
                action="open_application",
                application=app_target,
                speech_response=f"Opening {app_target} for you."
            )

        # Close application
        m_close = re.search(r"^(close|quit|stop|exit|kill)\s+(.+)$", clean)
        if m_close:
            app_target = m_close.group(2).strip()
            return IntentResponse(
                action="close_application",
                application=app_target,
                speech_response=f"Closing {app_target}."
            )

        # Volume controls
        m_vol = re.search(r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)", clean)
        if m_vol:
            val = int(m_vol.group(1))
            return IntentResponse(
                action="set_volume",
                value=val,
                speech_response=f"Setting volume to {val} percent."
            )
        if "increase volume" in clean or "volume up" in clean:
            return IntentResponse(action="increase_volume", speech_response="Increasing volume.")
        if "decrease volume" in clean or "volume down" in clean:
            return IntentResponse(action="decrease_volume", speech_response="Decreasing volume.")
        if "mute" in clean or "unmute" in clean:
            return IntentResponse(action="mute_volume", speech_response="Toggling audio mute.")

        # Brightness controls
        m_bright = re.search(r"(?:set\s+)?brightness\s+(?:to\s+)?(\d+)", clean)
        if m_bright:
            val = int(m_bright.group(1))
            return IntentResponse(
                action="set_brightness",
                value=val,
                speech_response=f"Setting brightness to {val} percent."
            )
        if "increase brightness" in clean or "brightness up" in clean:
            return IntentResponse(action="increase_brightness", speech_response="Increasing brightness.")
        if "decrease brightness" in clean or "brightness down" in clean:
            return IntentResponse(action="decrease_brightness", speech_response="Decreasing brightness.")

        # System controls
        if "screenshot" in clean:
            return IntentResponse(action="take_screenshot", speech_response="Taking a screenshot.")
        if "lock my pc" in clean or "lock pc" in clean or "lock workstation" in clean or clean == "lock":
            return IntentResponse(action="lock_pc", speech_response="Locking your PC.")
        if "trim memory" in clean or "optimize ram" in clean or "clear ram" in clean:
            return IntentResponse(action="trim_memory", speech_response="Trimming system memory.")
        if "system health" in clean or "health check" in clean:
            return IntentResponse(action="get_system_health", speech_response="Checking system health.")

        # ── Power controls ────────────────────────────────────────────────────
        if "hibernate" in clean:
            return IntentResponse(action="hibernate_pc", speech_response="Hibernating the PC.")
        if "cancel shutdown" in clean or "abort shutdown" in clean or "stop shutdown" in clean:
            return IntentResponse(action="cancel_shutdown", speech_response="Cancelling scheduled shutdown.")
        m_sd = re.search(r"shutdown\s+(?:after|in)\s+(\d+)", clean)
        if m_sd:
            mins = int(m_sd.group(1))
            return IntentResponse(action="shutdown_after", value=mins, speech_response=f"Shutting down in {mins} minutes.")
        m_rs = re.search(r"restart\s+(?:after|in)\s+(\d+)", clean)
        if m_rs:
            mins = int(m_rs.group(1))
            return IntentResponse(action="restart_after", value=mins, speech_response=f"Restarting in {mins} minutes.")
        if "power status" in clean or "charging status" in clean or ("battery" in clean and ("status" in clean or "check" in clean or "level" in clean)):
            return IntentResponse(action="check_power_status", speech_response="Checking power status.")
        if "uptime" in clean or "how long" in clean and "running" in clean or "boot time" in clean:
            return IntentResponse(action="check_uptime", speech_response="Checking system uptime.")
        if "battery" in clean:
            return IntentResponse(action="get_battery_status", speech_response="Checking battery status.")

        # ── Voice profile (Exclusive SARA Female Voice) ────────────────────────
        if "voice" in clean:
            return IntentResponse(action="switch_voice", query="default", speech_response="I operate exclusively with my dedicated SARA female voice profile.")

        # ── Audio controls ─────────────────────────────────────────────────────
        m_vol = re.search(r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)", clean)
        if m_vol:
            val = int(m_vol.group(1))
            return IntentResponse(action="set_volume", value=val, speech_response=f"Setting volume to {val} percent.")
        if "increase volume" in clean or "volume up" in clean or "louder" in clean or "raise volume" in clean:
            return IntentResponse(action="increase_volume", speech_response="Increasing volume.")
        if "decrease volume" in clean or "volume down" in clean or "quieter" in clean or "lower volume" in clean:
            return IntentResponse(action="decrease_volume", speech_response="Decreasing volume.")
        if "unmute" in clean and "mic" not in clean:
            return IntentResponse(action="unmute_volume", speech_response="Unmuting audio.")
        if "mute" in clean and "mic" not in clean:
            return IntentResponse(action="mute_volume", speech_response="Toggling audio mute.")
        if ("check volume" in clean or "what is the volume" in clean or "current volume" in clean or
                "volume level" in clean):
            return IntentResponse(action="get_volume_level", speech_response="Checking volume level.")
        if "change audio output" in clean or "switch speaker" in clean or "audio output" in clean:
            return IntentResponse(action="change_audio_output", speech_response="Opening audio output settings.")
        if "increase mic" in clean or "mic volume up" in clean or "microphone up" in clean:
            return IntentResponse(action="increase_mic_volume", speech_response="Increasing microphone volume.")
        if "decrease mic" in clean or "mic volume down" in clean or "microphone down" in clean:
            return IntentResponse(action="decrease_mic_volume", speech_response="Decreasing microphone volume.")
        if "unmute mic" in clean or "unmute microphone" in clean:
            return IntentResponse(action="unmute_microphone", speech_response="Microphone unmuted.")
        if "mute mic" in clean or "mute microphone" in clean:
            return IntentResponse(action="mute_microphone", speech_response="Toggling microphone mute.")

        # ── Brightness controls ────────────────────────────────────────────────
        m_bright = re.search(r"(?:set\s+)?brightness\s+(?:to\s+)?(\d+)", clean)
        if m_bright:
            val = int(m_bright.group(1))
            return IntentResponse(action="set_brightness", value=val, speech_response=f"Setting brightness to {val} percent.")
        if "increase brightness" in clean or "brightness up" in clean or "brighter" in clean:
            return IntentResponse(action="increase_brightness", speech_response="Increasing brightness.")
        if "decrease brightness" in clean or "brightness down" in clean or "dimmer" in clean:
            return IntentResponse(action="decrease_brightness", speech_response="Decreasing brightness.")
        if "check brightness" in clean or "brightness level" in clean or "current brightness" in clean:
            return IntentResponse(action="get_brightness_level", speech_response="Checking brightness level.")
        if "change resolution" in clean or "set resolution" in clean or "screen resolution" in clean:
            return IntentResponse(action="change_resolution", speech_response="Opening display settings.")
        if "night light on" in clean or "enable night light" in clean or "turn on night light" in clean:
            return IntentResponse(action="enable_night_light", speech_response="Enabling night light.")
        if "night light off" in clean or "disable night light" in clean or "turn off night light" in clean:
            return IntentResponse(action="disable_night_light", speech_response="Disabling night light.")
        if "detect monitors" in clean or "how many monitors" in clean or "connected monitors" in clean:
            return IntentResponse(action="detect_monitors", speech_response="Detecting monitors.")
        if "switch display" in clean or "extend screen" in clean or "duplicate screen" in clean or "display mode" in clean:
            q = ""
            for kw in ["extend", "duplicate", "mirror", "external", "second"]:
                if kw in clean:
                    q = kw
                    break
            return IntentResponse(action="switch_display_mode", query=q, speech_response="Switching display mode.")
        if "display info" in clean or "monitor info" in clean or "screen info" in clean:
            return IntentResponse(action="get_display_info", speech_response="Getting display information.")

        # ── Network controls ───────────────────────────────────────────────────
        if "wifi on" in clean or "turn on wifi" in clean or "enable wifi" in clean or "turn on wi-fi" in clean:
            return IntentResponse(action="wifi_on", speech_response="Turning Wi-Fi on.")
        if "wifi off" in clean or "turn off wifi" in clean or "disable wifi" in clean or "turn off wi-fi" in clean:
            return IntentResponse(action="wifi_off", speech_response="Turning Wi-Fi off.")
        if "show wifi" in clean or "available networks" in clean or "wifi networks" in clean or "wifi list" in clean:
            return IntentResponse(action="show_wifi_networks", speech_response="Showing available Wi-Fi networks.")
        m_con_wifi = re.search(r"connect\s+(?:to\s+)?(?:wifi\s+)?[\"']?(.+?)[\"']?\s*(?:wifi|network)?$", clean)
        if m_con_wifi and ("connect" in clean and ("wifi" in clean or "network" in clean)):
            ssid = m_con_wifi.group(1).strip()
            return IntentResponse(action="connect_wifi", query=ssid, speech_response=f"Connecting to {ssid}.")
        if "disconnect wifi" in clean or "disconnect from wifi" in clean:
            return IntentResponse(action="disconnect_wifi", speech_response="Disconnecting from Wi-Fi.")
        if "check internet" in clean or "am i connected" in clean or "internet connection" in clean:
            return IntentResponse(action="check_internet", speech_response="Checking internet connection.")
        if "my ip" in clean or "ip address" in clean or "show ip" in clean or "what is my ip" in clean:
            return IntentResponse(action="show_ip_address", speech_response="Getting IP address.")
        if "mac address" in clean or "my mac" in clean or "show mac" in clean:
            return IntentResponse(action="show_mac_address", speech_response="Getting MAC address.")
        if "internet speed" in clean or "test speed" in clean or "speed test" in clean or "network speed" in clean:
            return IntentResponse(action="test_network_speed", speech_response="Opening network speed test.")
        if "network settings" in clean or "open network" in clean:
            return IntentResponse(action="open_network_settings", speech_response="Opening network settings.")
        if "network" in clean or "wifi" in clean or "internet" in clean:
            return IntentResponse(action="get_network_status", speech_response="Checking network status.")

        # ── Bluetooth controls ─────────────────────────────────────────────────
        if ("bluetooth on" in clean or "turn on bluetooth" in clean or "enable bluetooth" in clean or
                "bt on" in clean):
            return IntentResponse(action="bluetooth_on", speech_response="Turning Bluetooth on.")
        if ("bluetooth off" in clean or "turn off bluetooth" in clean or "disable bluetooth" in clean or
                "bt off" in clean):
            return IntentResponse(action="bluetooth_off", speech_response="Turning Bluetooth off.")
        if "bluetooth devices" in clean or "show bluetooth" in clean or "paired devices" in clean:
            return IntentResponse(action="show_bluetooth_devices", speech_response="Listing Bluetooth devices.")
        if "connect bluetooth" in clean or ("connect" in clean and "bluetooth" in clean):
            q = re.sub(r"connect\s+(to\s+)?", "", clean).replace("bluetooth", "").strip()
            return IntentResponse(action="connect_bluetooth", query=q, speech_response="Opening Bluetooth settings to connect.")
        if "bluetooth settings" in clean or "open bluetooth" in clean:
            return IntentResponse(action="open_bluetooth_settings", speech_response="Opening Bluetooth settings.")

        # ── File management ────────────────────────────────────────────────────
        m_create = re.search(r"(?:create|make|new)\s+folder\s+(.+)", clean)
        if m_create:
            name = m_create.group(1).strip()
            return IntentResponse(action="create_folder", query=name, speech_response=f"Creating folder '{name}'.")
        m_rename = re.search(r"rename\s+(.+)\s+to\s+(.+)", clean)
        if m_rename:
            return IntentResponse(action="rename_file", query=clean.replace("rename ", ""),
                                  speech_response="Renaming file.")
        m_delete = re.search(r"(?:delete|remove)\s+(.+)", clean)
        if m_delete:
            target = m_delete.group(1).strip()
            return IntentResponse(action="delete_file", query=target, speech_response=f"Deleting '{target}'.")
        m_move = re.search(r"move\s+(.+)\s+to\s+(.+)", clean)
        if m_move:
            return IntentResponse(action="move_file", query=clean.replace("move ", ""),
                                  speech_response="Moving file.")
        m_copy = re.search(r"copy\s+(.+)\s+to\s+(.+)", clean)
        if m_copy:
            return IntentResponse(action="copy_file", query=clean.replace("copy ", ""),
                                  speech_response="Copying file.")
        m_search_file = re.search(r"(?:search|find)\s+(?:for\s+)?(?:file\s+)?(.+)", clean)
        if m_search_file and ("search for" in clean or "find file" in clean or "find the file" in clean):
            q = m_search_file.group(1).strip()
            return IntentResponse(action="search_files", query=q, speech_response=f"Searching for '{q}'.")
        if "recent files" in clean or "show recent" in clean or "recently opened" in clean:
            return IntentResponse(action="show_recent_files", speech_response="Opening recent files.")
        if "empty recycle" in clean or "clear recycle" in clean or "empty trash" in clean:
            return IntentResponse(action="empty_recycle_bin", speech_response="Emptying recycle bin.")
        m_zip = re.search(r"(?:zip|compress)\s+(.+)", clean)
        if m_zip:
            target = m_zip.group(1).strip()
            return IntentResponse(action="compress_files", query=target, speech_response=f"Compressing '{target}'.")
        m_unzip = re.search(r"(?:unzip|extract)\s+(.+)", clean)
        if m_unzip:
            target = m_unzip.group(1).strip()
            return IntentResponse(action="extract_zip", query=target, speech_response=f"Extracting '{target}'.")

        # ── Browser / web shortcuts ────────────────────────────────────────────
        if "linkedin" in clean:
            return IntentResponse(action="open_linkedin", speech_response="Opening LinkedIn.")
        if "wikipedia" in clean:
            m_wiki = re.search(r"(?:search\s+)?wikipedia\s+(?:for\s+)?(.+)", clean)
            q = m_wiki.group(1).strip() if m_wiki else ""
            return IntentResponse(action="search_wikipedia", query=q, speech_response=f"Searching Wikipedia for {q}." if q else "Opening Wikipedia.")
        if "weather" in clean:
            return IntentResponse(action="check_weather", speech_response="Checking weather.")
        m_dl = re.search(r"download\s+(https?://\S+)", clean)
        if m_dl:
            url = m_dl.group(1)
            return IntentResponse(action="download_file", query=url, speech_response="Starting download.")

        # ── System monitoring ──────────────────────────────────────────────────
        if "cpu usage" in clean or "cpu stats" in clean or "processor usage" in clean:
            return IntentResponse(action="get_cpu_usage", speech_response="Checking CPU usage.")
        if "ram usage" in clean or "memory usage" in clean or "how much ram" in clean:
            return IntentResponse(action="get_ram_usage", speech_response="Checking RAM usage.")
        if "disk" in clean and ("usage" in clean or "free" in clean or "space" in clean):
            return IntentResponse(action="get_disk_usage", speech_response="Checking disk space.")
        if "available storage" in clean or "free storage" in clean or "storage space" in clean:
            return IntentResponse(action="get_available_storage", speech_response="Checking available storage.")
        if "cpu temp" in clean or "cpu temperature" in clean or "processor temp" in clean:
            return IntentResponse(action="get_cpu_temperature", speech_response="Checking CPU temperature.")
        if "running apps" in clean or "what is running" in clean or "show processes" in clean or "open apps" in clean:
            return IntentResponse(action="show_running_apps", speech_response="Showing running applications.")
        m_kill = re.search(r"(?:kill|end task|close process|terminate)\s+(.+)", clean)
        if m_kill:
            proc = m_kill.group(1).strip()
            return IntentResponse(action="kill_process", query=proc, application=proc,
                                  speech_response=f"Terminating {proc}.")
        if "laptop specs" in clean or "system specs" in clean or "my specs" in clean or "pc specs" in clean:
            return IntentResponse(action="get_laptop_specs", speech_response="Getting laptop specifications.")
        if "windows version" in clean or "what version" in clean or "os version" in clean:
            return IntentResponse(action="get_windows_version", speech_response="Checking Windows version.")
        if "clear temp" in clean or "clean temp" in clean or "delete temp" in clean or "temp files" in clean:
            return IntentResponse(action="clear_temp_files", speech_response="Clearing temporary files.")
        if "record screen" in clean or "start recording" in clean or "screen record" in clean:
            return IntentResponse(action="record_screen", speech_response="Opening screen recorder.")
        if "stop recording" in clean or "end recording" in clean:
            return IntentResponse(action="stop_recording", speech_response="Stopping screen recording.")
        if "screen share" in clean or "share screen" in clean or "screen sharing" in clean:
            return IntentResponse(action="start_screen_sharing", speech_response="Opening screen sharing.")

        # ── File automation ────────────────────────────────────────────────────
        if "organise" in clean or "organize" in clean:
            return IntentResponse(action="organize_downloads", speech_response="Organizing your downloads folder.")
        if "large files" in clean or "find large" in clean:
            return IntentResponse(action="find_large_files", speech_response="Searching for large files.")

        # ── Routines ───────────────────────────────────────────────────────────
        if "routine" in clean or "mode" in clean:
            for r_name in ["morning", "work", "night", "dev setup", "presentation", "lock and go", "focus"]:
                if r_name in clean:
                    return IntentResponse(
                        action="run_routine",
                        query=r_name,
                        speech_response=f"Activating {r_name} routine."
                    )

        # YouTube / Google Search
        m_yt = re.search(r"search\s+youtube\s+for\s+(.+)", clean)
        if m_yt:
            q = m_yt.group(1).strip()
            return IntentResponse(action="search_youtube", query=q, speech_response=f"Searching YouTube for {q}.")
        m_g = re.search(r"search\s+(?:google\s+for\s+)?(.+)", clean)
        if m_g and ("search" in clean or "google" in clean):
            q = m_g.group(1).strip()
            return IntentResponse(action="search_google", query=q, speech_response=f"Searching Google for {q}.")

        # ── Bare app name ─ e.g. user just says "telegram" or "whatsapp" ───────
        # Matches 1-3 word inputs that look like an app name (not a question/sentence)
        KNOWN_BARE_APPS = [
            "chrome", "firefox", "edge", "telegram", "whatsapp", "discord",
            "spotify", "vlc", "notepad", "calculator", "word", "excel",
            "powerpoint", "vscode", "vs code", "intellij", "android studio",
            "capcut", "zoom", "teams", "skype", "steam", "epic games",
            "winrar", "7-zip", "potplayer", "brave", "opera"
        ]
        clean_words = clean.split()
        if len(clean_words) <= 3 and not any(c in clean for c in ["?", "what", "how", "why", "when", "who", "tell", "explain"]):
            for app in KNOWN_BARE_APPS:
                if clean == app or clean.startswith(app):
                    return IntentResponse(
                        action="open_application",
                        application=clean,
                        speech_response=f"Opening {clean.title()}."
                    )

        return None
