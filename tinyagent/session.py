"""Session persistence — JSON files in .tinyagent-sessions/.

Keeps things inspectable with standard Unix tools. No databases."""

from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SESSIONS_DIR = Path(".tinyagent-sessions")


class Session:
    """Persistent session state for an agent run."""

    def __init__(self, session_id: str,
                 messages: list[dict[str, Any]] | None = None,
                 tool_results: list[dict[str, Any]] | None = None,
                 metadata: dict[str, Any] | None = None) -> None:
        self.session_id = session_id
        self.messages: list[dict[str, Any]] = messages or []
        self.tool_results: list[dict[str, Any]] = tool_results or []
        self.metadata: dict[str, Any] = metadata or {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def new(cls) -> Session:
        return cls(session_id=str(uuid.uuid4()))

    @classmethod
    def load(cls, session_id: str) -> Session:
        """Load from disk. Raises FileNotFoundError if missing."""
        path = SESSIONS_DIR / f"{session_id}.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(session_id=data["session_id"], messages=data.get("messages", []),
                   tool_results=data.get("tool_results", []), metadata=data.get("metadata", {}))

    def save(self) -> Path:
        """Write session state to disk."""
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self.metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        data = {"session_id": self.session_id, "messages": self.messages,
                "tool_results": self.tool_results, "metadata": self.metadata}
        path = SESSIONS_DIR / f"{self.session_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    @staticmethod
    def list_sessions() -> list[dict[str, Any]]:
        if not SESSIONS_DIR.exists():
            return []
        sessions = []
        for path in sorted(SESSIONS_DIR.glob("*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({"session_id": data["session_id"],
                                 "created_at": data.get("metadata", {}).get("created_at"),
                                 "message_count": len(data.get("messages", []))})
            except (json.JSONDecodeError, KeyError):
                continue
        return sessions

    def record_message(self, role: str, content: Any) -> None:
        self.messages.append({"role": role, "content": content,
                              "timestamp": datetime.now(timezone.utc).isoformat()})

    def record_tool_result(self, tool_use_id: str, name: str,
                           input_args: Any, output: Any) -> None:
        self.tool_results.append({"id": tool_use_id, "name": name, "input": input_args,
                                  "output": str(output),
                                  "timestamp": datetime.now(timezone.utc).isoformat()})
