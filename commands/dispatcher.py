"""
Command Dispatcher — Routes AI intent to the correct command handler.
Acts as the bridge between the AI engine output and actual system operations.
"""

from typing import Dict, Any, Optional
from ai.schemas import IntentResponse
from commands.base import BaseCommand
from config import config
from utils.logger import logger


class CommandDispatcher:
    """
    Central dispatcher that maps action keys to registered command handlers
    and executes them with confirmation checks for dangerous operations.
    """

    def __init__(self):
        self._registry: Dict[str, BaseCommand] = {}
        logger.info("CommandDispatcher initialized.")

    def register(self, command: BaseCommand) -> None:
        """Register a command handler by its action_name."""
        self._registry[command.action_name] = command
        logger.debug(f"Registered command: '{command.action_name}'")

    def dispatch(self, intent: IntentResponse) -> Dict[str, Any]:
        """
        Execute the command matching the intent action.
        Returns a result payload dict with status, message, and data.
        """
        action = intent.action

        # Safety check for dangerous operations
        if action in config.security.REQUIRE_CONFIRMATION_FOR and not intent.requires_confirmation:
            logger.warning(f"Dangerous action '{action}' blocked — confirmation required.")
            return {
                "status": "confirmation_required",
                "action": action,
                "message": f"This action requires your confirmation: '{action}'"
            }

        handler = self._registry.get(action)
        if not handler:
            logger.info(f"No handler registered for action: '{action}'")
            return {
                "status": "not_implemented",
                "action": action,
                "message": f"Action '{action}' is not yet implemented."
            }

        try:
            params = {
                "application": intent.application,
                "value": intent.value,
                "query": intent.query,
                **intent.params
            }
            result = handler.execute({k: v for k, v in params.items() if v is not None})
            logger.info(f"Command '{action}' executed -> status: {result.get('status')}")
            return result
        except Exception as e:
            logger.error(f"Command '{action}' raised exception: {e}", exc_info=True)
            return {
                "status": "error",
                "action": action,
                "message": f"Command failed: {str(e)}"
            }

    def list_registered(self) -> list[str]:
        """Return list of all registered action keys."""
        return list(self._registry.keys())
