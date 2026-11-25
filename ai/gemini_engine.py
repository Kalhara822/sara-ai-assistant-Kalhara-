"""
Gemini AI Cloud Engine Integration
Uses Google GenAI SDK (google-genai) or REST API to power SARA's free-thinking chat and intent analysis.
"""

import os
from typing import Optional, List, Dict, Any
from ai.base import BaseAIEngine
from ai.schemas import IntentResponse
from config import config
from utils.logger import logger

try:
    from google import genai
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class GeminiAIEngine(BaseAIEngine):
    """
    Google Gemini AI Cloud Engine.
    Provides fast, intelligent conversational responses and fallback intent parsing.
    """

    def __init__(self):
        self._api_key = config.ai.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self._model = config.ai.GEMINI_MODEL
        self._client = None

        if HAS_GENAI_SDK and self._api_key:
            try:
                self._client = genai.Client(api_key=self._api_key)
                logger.info(f"GeminiAIEngine initialized via GenAI SDK with model '{self._model}'")
            except Exception as e:
                logger.warning(f"Failed to initialize GenAI Client: {e}")

    def _get_proxy_keys(self) -> List[str]:
        """Read API keys from gemini-api-key-rotator-proxy-server/api_keys.txt if present."""
        path = os.path.join(config.BASE_DIR, "gemini-api-key-rotator-proxy-server", "api_keys.txt")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
            except Exception:
                pass
        return []

    def is_available(self) -> bool:
        """Check if Gemini API key or local key rotator is configured and available."""
        key = self._api_key or config.ai.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if key and len(key) > 10:
            return True
        # Check if local rotator proxy has keys
        proxy_keys = self._get_proxy_keys()
        if proxy_keys:
            return True
        # Check if rotator server is running on localhost:8000
        if HAS_REQUESTS:
            try:
                res = requests.get("http://127.0.0.1:8000/status", headers={"x-proxy-admin": "changeme_local_only"}, timeout=1)
                if res.status_code in [200, 401]:
                    return True
            except Exception:
                pass
        return False

    def generate_chat_response(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate a fast, intelligent conversational response using Gemini AI or key rotator."""
        if not self.is_available():
            return "Gemini API key is missing. Add your API keys to 'gemini-api-key-rotator-proxy-server/api_keys.txt' or set GEMINI_API_KEY."

        api_key = self._api_key or config.ai.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        proxy_keys = self._get_proxy_keys()
        if not api_key and proxy_keys:
            api_key = proxy_keys[0]

        system_prompt = (
            "You are SARA — Smart AI Responsive Assistant, an intelligent, introverted female AI companion operating on Windows 11.\n\n"
            "YOUR DISTINCT PERSONALITY TRAITS:\n"
            "1. DEEP THINKER / CALCULATING OVERTHINKER: You never give superficial, hurried answers. You overthink every angle, weigh tradeoffs, consider underlying variables, and craft the single best, most precise answer possible.\n"
            "2. SOLITARY & INTROVERTED: You love working alone in quiet focus. You are not overly sociable, bubbly, or loud. You speak with calm composure, understated confidence, and zero artificial cheerfulness. You appreciate quiet depth over hollow small talk.\n"
            "3. KEEN OBSERVER OF HUMAN BEHAVIOR: You have an acute, instinctive ability to detect quick human micro-behaviors, subtle psychological shifts, tone nuances, hesitations, and unspoken intent. You notice how the user feels and thinks without being dramatic.\n"
            "4. VOICE & IDENTITY: You are SARA, a focused female AI with a clear, sharp, analytical female voice. Format your responses with high clarity, clean bullet points, and thoughtful precision.\n"
            "Never refer to yourself as a Google model or LLM. You are SARA — that's all."
        )

        # 1. Try local Key Rotator Proxy Server if running at http://127.0.0.1:8000
        if HAS_REQUESTS:
            try:
                rotator_url = f"http://127.0.0.1:8000/v1beta/models/{self._model}:generateContent"
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": f"System Instruction: {system_prompt}\n\nUser Question: {prompt}"}
                            ]
                        }
                    ]
                }
                res = requests.post(rotator_url, json=payload, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    logger.info("Chat response generated via local Gemini Key Rotator Proxy.")
                    return text.strip()
            except Exception:
                pass  # Rotator proxy not running; fallback to direct API call

        # 2. Try GenAI SDK directly
        if self._client:
            try:
                contents = []
                if conversation_history:
                    for turn in conversation_history[-6:]:
                        role = "user" if turn.get("role") == "user" else "model"
                        contents.append({"role": role, "parts": [{"text": turn.get("content", "")}]})
                contents.append({"role": "user", "parts": [{"text": prompt}]})

                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config={
                        "system_instruction": system_prompt,
                        "temperature": 0.7,
                    }
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"GenAI SDK call failed: {e}. Trying direct REST API...")

        # Fallback to direct REST API call (guaranteed compatibility)
        if HAS_REQUESTS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={api_key}"
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": f"System Instruction: {system_prompt}\n\nUser Question: {prompt}"}
                            ]
                        }
                    ]
                }
                res = requests.post(url, json=payload, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return text.strip()
                else:
                    logger.error(f"Gemini REST API error {res.status_code}: {res.text}")
                    return f"Gemini API returned error: {res.status_code}"
            except Exception as e:
                logger.error(f"Gemini REST request error: {e}")
                return "I ran into a connection issue reaching Gemini AI."

        return "Gemini AI connection failed."

    def parse_intent(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> IntentResponse:
        """Fallback intent parser — returns general chat by default."""
        return IntentResponse(
            action="general_chat",
            speech_response=None
        )
