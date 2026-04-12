"""Tool: run_command — shell command via subprocess with timeout.

TODO: subprocess sandboxing — see memex/active-threads/tool-use-governance.md
    This is the most dangerous tool. Production needs: command allowlists,
    filesystem sandboxing, network controls, resource limits.
"""

import subprocess
from typing import Any
from tinyagent.tools import registry

DEFAULT_TIMEOUT_S = 30


def handle_run_command(args: dict[str, Any]) -> str:
    command = args.get("command", "")
    timeout = args.get("timeout", DEFAULT_TIMEOUT_S)
    if not command:
        return "Error: 'command' is required."

    try:
        result = subprocess.run(command, shell=True, capture_output=True,
                                text=True, timeout=timeout)
        parts = []
        if result.stdout:
            parts.append(result.stdout)
        if result.stderr:
            parts.append(f"[stderr]\n{result.stderr}")
        if result.returncode != 0:
            parts.append(f"[exit code: {result.returncode}]")
        return "\n".join(parts) if parts else "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s"
    except OSError as e:
        return f"Error running command: {e}"


registry.register(
    name="run_command",
    description="Run a shell command. Returns stdout/stderr with configurable timeout.",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute."},
            "timeout": {"type": "number", "description": "Timeout in seconds (default: 30)."},
        },
        "required": ["command"],
    },
    handler=handle_run_command,
)
