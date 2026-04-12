"""Tool: write_file — write content to a file. Refuses paths outside cwd."""

import os
from pathlib import Path
from typing import Any
from tinyagent.tools import registry


def handle_write_file(args: dict[str, Any]) -> str:
    file_path = args.get("path", "")
    content = args.get("content", "")
    if not file_path:
        return "Error: 'path' is required."

    target = Path(file_path).resolve()
    cwd = Path(os.getcwd()).resolve()
    try:
        target.relative_to(cwd)
    except ValueError:
        return f"Error: refusing to write outside working directory ({target})"

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except OSError as e:
        return f"Error writing file: {e}"
    return f"Wrote {len(content)} chars to {target}"


registry.register(
    name="write_file",
    description="Write content to a file. Refuses paths outside the working directory.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path (relative to cwd)."},
            "content": {"type": "string", "description": "Content to write."},
        },
        "required": ["path", "content"],
    },
    handler=handle_write_file,
)
