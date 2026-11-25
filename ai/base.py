"""
Abstract Base Class for SARA AI Engine
Enforces SOLID principles (Interface Segregation & Dependency Inversion)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ai.schemas import IntentResponse

class BaseAIEngine(ABC):
    """Abstract contract for LLM provider implementations."""

    @abstractmethod
    def parse_intent(self, user_input: str, conversation_history: List[Dict[str, str]] = None) -> IntentResponse:
        """Parse natural language user input into structured IntentResponse."""
        pass

    @abstractmethod
    def generate_chat_response(self, prompt: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """Generate conversational response for free-form dialogue."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if LLM engine service (e.g. Ollama daemon) is online."""
        pass
