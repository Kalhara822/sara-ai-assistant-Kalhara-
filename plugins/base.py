"""
Abstract Base Class & Registry for Modular Extensions (Plugins)
Enables single-file plugin creation and auto-registration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Type, List, Optional
from utils.logger import logger

class BasePlugin(ABC):
    """Abstract base class for all SARA plugins."""

    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Unique human-readable plugin identifier."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin semantic version."""
        pass

    @property
    @abstractmethod
    def supported_actions(self) -> List[str]:
        """List of intent action strings handled by this plugin."""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """Lifecycle hook called when plugin is loaded."""
        pass

    @abstractmethod
    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specified action handled by this plugin."""
        pass


class PluginManager:
    """Auto-discovery and registration manager for SARA plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, BasePlugin] = {}
        self._action_map: Dict[str, BasePlugin] = {}

    def register_plugin(self, plugin: BasePlugin) -> bool:
        """Register a plugin instance."""
        try:
            if not plugin.initialize():
                logger.warning(f"Plugin {plugin.plugin_name} failed initialization.")
                return False

            self._plugins[plugin.plugin_name] = plugin
            for action in plugin.supported_actions:
                self._action_map[action] = plugin

            logger.info(f"Registered plugin: {plugin.plugin_name} (v{plugin.version}) handling actions: {plugin.supported_actions}")
            return True
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin.plugin_name}: {e}")
            return False

    def get_plugin_for_action(self, action: str) -> Optional[BasePlugin]:
        """Retrieve registered plugin handling specified action."""
        return self._action_map.get(action)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List summary of all loaded plugins."""
        return [
            {
                "name": p.plugin_name,
                "version": p.version,
                "actions": p.supported_actions
            }
            for p in self._plugins.values()
        ]
