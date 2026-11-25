"""
Abstract Base Class for SARA Commands & Actions
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseCommand(ABC):
    """Base interface for all internal system commands."""

    @property
    @abstractmethod
    def action_name(self) -> str:
        """Unique action key matching LLM intent (e.g. 'open_application')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the command."""
        pass

    @property
    def requires_confirmation(self) -> bool:
        """Default safety check requirement."""
        return False

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute command with parameters.
        Returns result payload dictionary containing status, message, and telemetry data.
        """
        pass
