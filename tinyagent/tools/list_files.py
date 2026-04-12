"""Tool: list_files — glob-based file listing."""

import os
from pathlib import Path
from typing import Any
from tinyagent.tools import registry

MAX_RESULTS = 200


def handle_list_files(args: dict[str, Any]) -> str:
    pattern = args.get("pattern", "**/*")
    directory = args.get("directory", ".")
    base = Path(directory).resolve()

    if not base.is_dir():
        return f"Error: not a directory: {base}"

    try:
        matches = sorted(base.glob(pattern))
    except ValueError as e:
        return f"Error: invalid glob pattern: {e}"

    files = [p for p in matches if p.is_file()]
    cwd = Path(os.getcwd()).resolve()
    lines = []
    for f in files[:MAX_RESULTS]:
        try:
            lines.append(str(f.relative_to(cwd)))
        except ValueError:
            lines.append(str(f))

    if len(files) > MAX_RESULTS:
        lines.append(f"\n[Truncated: {len(files)} matched, showing {MAX_RESULTS}]")
    return "\n".join(lines) if lines else "(no matching files)"


registry.register(
    name="list_files",
    description="List files matching a glob pattern, relative to working directory.",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern (default: '**/*')."},
            "directory": {"type": "string", "description": "Base directory (default: '.')."},
        },
        "required": [],
    },
    handler=handle_list_files,
)
