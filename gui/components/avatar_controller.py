"""
AI Avatar Animation Controller
Analyzes AI responses and determines facial reaction blendshapes, emotions, and colors for GUI rendering.
"""

import json
from typing import Dict, Any, Tuple


class AIAvatarAnimationController:
    """Controls AI avatar emotional states and facial rig blendshape parameters."""

    def __init__(self):
        self.current_emotion = "NEUTRAL"

        # Facial blendshape / parameter mappings for Live2D, Pygame, or Tkinter Canvas
        self.expression_presets: Dict[str, Dict[str, Any]] = {
            "NEUTRAL":   {"eye_open": 1.0, "mouth_smile": 0.1, "eyebrow_slant": 0.0, "blush": 0.0, "color": "#00E5FF", "symbol": "⚙️"},
            "HAPPY":     {"eye_open": 0.8, "mouth_smile": 0.9, "eyebrow_slant": 0.2, "blush": 0.3, "color": "#00E676", "symbol": "😊"},
            "SURPRISED": {"eye_open": 1.3, "mouth_smile": 0.6, "eyebrow_slant": 0.8, "blush": 0.0, "color": "#FFD700", "symbol": "😲"},
            "SAD":       {"eye_open": 0.5, "mouth_smile": -0.5, "eyebrow_slant": -0.4, "blush": 0.0, "color": "#64B5F6", "symbol": "🥺"},
            "ANGRY":     {"eye_open": 0.9, "mouth_smile": -0.3, "eyebrow_slant": -0.7, "blush": 0.0, "color": "#FF5252", "symbol": "😠"},
            "BLUSHING":  {"eye_open": 0.7, "mouth_smile": 0.5, "eyebrow_slant": 0.1, "blush": 1.0, "color": "#FF4081", "symbol": "😳"}
        }

    def detect_emotion(self, text_response: str) -> str:
        """Analyzes text response to select appropriate facial reaction."""
        text_lower = text_response.lower()
        if any(w in text_lower for w in ["happy", "great", "awesome", "yay", "love", "excellent", "wonderful", "glad", "enjoy", "smile", "super"]):
            return "HAPPY"
        elif any(w in text_lower for w in ["what", "wow", "really", "omg", "huh", "surprised", "unexpected", "amazing", "whoa"]):
            return "SURPRISED"
        elif any(w in text_lower for w in ["sad", "sorry", "unfortunately", "bad", "apologize", "regret", "fail", "unhappy"]):
            return "SAD"
        elif any(w in text_lower for w in ["angry", "stop", "annoyed", "hate", "error", "failed", "danger", "warning", "mad"]):
            return "ANGRY"
        elif any(w in text_lower for w in ["shy", "flustered", "cute", "embarrassed", "blush", "sweet", "blushing"]):
            return "BLUSHING"
        return "NEUTRAL"

    def update_facial_reaction(self, text_response: str) -> Tuple[str, Dict[str, Any]]:
        """Calculates emotion state and outputs rendering parameters."""
        emotion = self.detect_emotion(text_response)
        self.current_emotion = emotion
        facial_params = self.expression_presets[emotion]
        return emotion, facial_params
