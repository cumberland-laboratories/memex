"""Tool registry — register tools, get schemas, execute by name.

Tools are plain functions with JSON Schema metadata. No classes,
no inheritance. A tool is: name + description + schema + handler."""

from __future__ import annotations
from typing import Any, Callable


class _ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def register(self, name: str, description: str,
                 parameters: dict[str, Any],
                 handler: Callable[[dict[str, Any]], str]) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = {"name": name, "description": description,
                             "parameters": parameters, "handler": handler}

    def get_schemas(self) -> list[dict[str, Any]]:
        """Tool definitions in Anthropic API format."""
        return [{"name": t["name"], "description": t["description"],
                 "input_schema": t["parameters"]} for t in self._tools.values()]

    def execute(self, name: str, args: dict[str, Any]) -> str:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]["handler"](args)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())


registry = _ToolRegistry()


def load_all_tools() -> None:
    """Import built-in tool modules to trigger self-registration."""
    from tinyagent.tools import read_file, write_file, run_command, list_files  # noqa: F401

load_all_tools()
