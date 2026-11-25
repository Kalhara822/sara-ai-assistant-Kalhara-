"""
Plugin Auto-Discovery & Loader System
Scans the plugins/ directory for valid plugin files and auto-registers them.
Adding a new command requires creating ONLY one .py file in the plugins/ folder.
"""

import importlib
import importlib.util
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from plugins.base import BasePlugin, PluginManager
from commands.base import BaseCommand
from commands.dispatcher import CommandDispatcher
from config import config
from utils.logger import logger


class PluginLoader:
    """
    Scans the plugins/ directory, dynamically imports all valid plugin modules,
    and registers their commands with the CommandDispatcher.
    """

    def __init__(self, dispatcher: CommandDispatcher, plugin_manager: PluginManager):
        self._dispatcher = dispatcher
        self._plugin_manager = plugin_manager
        self._loaded_plugins: List[str] = []
        self._failed_plugins: List[Dict[str, str]] = []

    def discover_and_load(self) -> Dict[str, Any]:
        """
        Walk the plugins/ directory and auto-load every valid plugin file.
        Returns a summary dict of loaded/failed counts.
        """
        plugins_dir = config.PLUGINS_DIR
        logger.info(f"Scanning plugin directory: {plugins_dir}")

        plugin_files = [
            f for f in plugins_dir.iterdir()
            if f.suffix == ".py" and not f.name.startswith("_")
        ]

        for plugin_file in plugin_files:
            self._load_plugin_file(plugin_file)

        logger.info(
            f"Plugin discovery complete — "
            f"Loaded: {len(self._loaded_plugins)}, "
            f"Failed: {len(self._failed_plugins)}"
        )

        return {
            "loaded": self._loaded_plugins,
            "failed": self._failed_plugins,
            "total": len(plugin_files),
        }

    def _load_plugin_file(self, plugin_file: Path) -> bool:
        """Dynamically import a single plugin file and register its contents."""
        module_name = f"plugins.dynamic.{plugin_file.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            registered = False

            # Register any BasePlugin subclasses found in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr is not BasePlugin
                ):
                    try:
                        instance = attr()
                        success = self._plugin_manager.register_plugin(instance)
                        if success:
                            # Also register plugin's commands with dispatcher
                            for action in instance.supported_actions:
                                # Plugin acts as its own command handler via adapter
                                self._dispatcher.register(
                                    PluginCommandAdapter(instance, action)
                                )
                            registered = True
                    except Exception as e:
                        logger.error(f"Plugin class '{attr_name}' init failed: {e}", exc_info=True)

                # Also register standalone BaseCommand subclasses
                elif (
                    isinstance(attr, type)
                    and issubclass(attr, BaseCommand)
                    and attr is not BaseCommand
                    and not registered
                ):
                    try:
                        cmd_instance = attr()
                        self._dispatcher.register(cmd_instance)
                        registered = True
                    except Exception as e:
                        logger.error(f"Command class '{attr_name}' init failed: {e}")

            if registered:
                self._loaded_plugins.append(plugin_file.stem)
                logger.info(f"Plugin loaded: '{plugin_file.stem}'")
            else:
                logger.warning(f"No valid plugin/command classes found in: '{plugin_file.name}'")

            return registered

        except Exception as e:
            error_msg = str(e)
            self._failed_plugins.append({"file": plugin_file.name, "error": error_msg})
            logger.error(f"Failed to load plugin '{plugin_file.name}': {error_msg}", exc_info=True)
            return False

    @property
    def loaded_plugins(self) -> List[str]:
        return self._loaded_plugins

    @property
    def failed_plugins(self) -> List[Dict[str, str]]:
        return self._failed_plugins


class PluginCommandAdapter(BaseCommand):
    """
    Adapts a BasePlugin instance into a BaseCommand interface
    so plugin actions can be registered in the CommandDispatcher.
    """

    def __init__(self, plugin: BasePlugin, action: str):
        self._plugin = plugin
        self._action = action

    @property
    def action_name(self) -> str:
        return self._action

    @property
    def description(self) -> str:
        return f"[Plugin: {self._plugin.plugin_name}] — {self._action}"

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._plugin.execute_action(self._action, params)
