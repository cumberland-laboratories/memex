"""Tool: read_file — read a file, truncate if over budget."""

from pathlib import Path
from typing import Any
from tinyagent.tools import registry

MAX_CHARS = 50_000  # ~12,500 tokens


def handle_read_file(args: dict[str, Any]) -> str:
    file_path = args.get("path", "")
    if not file_path:
        return "Error: 'path' is required."
    path = Path(file_path).resolve()
    if not path.exists():
        return f"Error: file not found: {path}"
    if not path.is_file():
        return f"Error: not a regular file: {path}"
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"Error reading file: {e}"

    if len(content) > MAX_CHARS:
        truncated = content[:MAX_CHARS]
        return (truncated + f"\n\n[Truncated: {truncated.count(chr(10))}/{content.count(chr(10))} "
                f"lines, {MAX_CHARS}/{len(content)} chars]")
    return content


registry.register(
    name="read_file",
    description="Read a file's contents. Truncates if very large.",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Path to the file."}},
        "required": ["path"],
    },
    handler=handle_read_file,
)
