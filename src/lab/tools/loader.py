"""Dynamic tool loading for OpenHands Lab."""

import importlib.util
import sys
from pathlib import Path
from typing import Any

from openhands.sdk import register_tool, ToolDefinition

from lab.tools.base import BaseLabTool


class ToolLoader:
    """Dynamically loads custom tools from a directory.

    Scans a directory for Python files containing BaseLabTool subclasses
    and registers them with the OpenHands SDK tool registry.
    """

    def __init__(self, tools_dir: str | Path = "src/lab/tools"):
        self.tools_dir = Path(tools_dir)
        self._loaded_tools: dict[str, type[BaseLabTool[Any, Any]]] = {}

    @property
    def loaded_tools(self) -> dict[str, type[BaseLabTool[Any, Any]]]:
        """Get all loaded tool classes."""
        return self._loaded_tools

    def scan_and_load(self) -> list[str]:
        """Scan the tools directory and load all custom tools.

        Returns:
            List of registered tool names
        """
        if not self.tools_dir.exists():
            return []

        registered = []
        for py_file in self.tools_dir.glob("*.py"):
            # Skip __init__.py and base.py
            if py_file.name.startswith("_") or py_file.name in (
                "base.py",
                "loader.py",
            ):
                continue

            tools = self._load_tools_from_file(py_file)
            for tool_cls in tools:
                name = self._register_tool(tool_cls)
                registered.append(name)

        return registered

    def _load_tools_from_file(
        self, file_path: Path
    ) -> list[type[BaseLabTool[Any, Any]]]:
        """Load tool classes from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            List of BaseLabTool subclasses found in the file
        """
        module_name = f"lab.tools.{file_path.stem}"

        # Reuse existing module if already imported
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return []

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module

            try:
                spec.loader.exec_module(module)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")
                return []

        # Find all BaseLabTool subclasses in the module
        tools = []
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseLabTool)
                and obj is not BaseLabTool
                and hasattr(obj, "create")
            ):
                tools.append(obj)

        return tools

    def _register_tool(self, tool_cls: type[BaseLabTool[Any, Any]]) -> str:
        """Register a tool class with the SDK.

        Args:
            tool_cls: The tool class to register

        Returns:
            The registered tool name
        """
        name = tool_cls.get_name()

        # Create a factory function for the SDK
        def factory(conv_state: Any, **params: Any) -> list[ToolDefinition[Any, Any]]:
            return list(tool_cls.create(conv_state, **params))

        register_tool(name, factory)
        self._loaded_tools[name] = tool_cls

        return name

    def reload_tool(self, file_path: str | Path) -> list[str]:
        """Reload tools from a specific file.

        Used for hot-reloading when a file changes.

        Args:
            file_path: Path to the modified Python file

        Returns:
            List of reloaded tool names
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return []

        # Remove old module from cache if present
        module_name = f"lab.tools.{file_path.stem}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Reload tools from file
        tools = self._load_tools_from_file(file_path)
        registered = []
        for tool_cls in tools:
            name = self._register_tool(tool_cls)
            registered.append(name)

        return registered

    def get_tool_info(self) -> list[dict[str, str]]:
        """Get information about all loaded tools.

        Returns:
            List of dicts with name and description
        """
        return [
            {
                "name": name,
                "description": cls.get_description(),
            }
            for name, cls in self._loaded_tools.items()
        ]
