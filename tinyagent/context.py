"""Context-budget manager — the headline design concern.

The core tension: Claude has a fixed context window, but an agentic loop
accumulates messages without bound. This module decides what stays, what
gets summarized, and what gets dropped.

Three priority tiers:
    PINNED     system prompt, tool schemas     (never evicted)
    RECENT     last N turns                    (kept verbatim)
    HISTORICAL older turns                     (compressible)
"""

from __future__ import annotations
import enum
from dataclasses import dataclass
from typing import Any

MODEL_MAX_TOKENS = {"claude-sonnet-4-20250514": 200_000, "claude-haiku-4-20250414": 200_000}
DEFAULT_MAX_TOKENS = 200_000
OUTPUT_RESERVE = 8_192
RECENT_TURN_COUNT = 6


class Priority(enum.IntEnum):
    PINNED = 0      # system prompt, tool schemas
    RECENT = 1      # last N turns
    HISTORICAL = 2  # compressible


@dataclass
class TrackedMessage:
    role: str
    content: Any
    priority: Priority
    token_estimate: int = 0
    turn_index: int = 0
    # TODO: real token counting — see memex/active-threads/context-budget-economics.md
    #   chars/4 is a crude heuristic; production needs anthropic.count_tokens()


class ContextManager:
    """Tracks all messages and enforces the token budget."""

    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        self.budget = MODEL_MAX_TOKENS.get(model, DEFAULT_MAX_TOKENS) - OUTPUT_RESERVE
        self._messages: list[TrackedMessage] = []
        self._turn_counter: int = 0

    def add(self, role: str, content: Any, priority: Priority = Priority.RECENT) -> None:
        """Append a message. Auto-compacts if over budget."""
        msg = TrackedMessage(
            role=role, content=content, priority=priority,
            token_estimate=self._estimate_tokens(content),
            turn_index=self._turn_counter,
        )
        self._turn_counter += 1
        self._messages.append(msg)
        if self._total_tokens() > self.budget:
            self.compact()

    def compact(self) -> None:
        """Summarize historical messages to free budget space.

        TODO: formal cost model — see memex/active-threads/context-budget-economics.md
            A real system needs to weigh: cost of re-summarization vs. lost detail,
            which tool results are "load-bearing", whether the goal has shifted.
        """
        self._reassign_priorities()
        historical = [m for m in self._messages if m.priority == Priority.HISTORICAL]
        if not historical:
            return

        summary_text = self._build_summary_stub(historical)
        self._messages = [m for m in self._messages if m.priority != Priority.HISTORICAL]

        summary = TrackedMessage(
            role="assistant", content=summary_text, priority=Priority.HISTORICAL,
            token_estimate=self._estimate_tokens(summary_text), turn_index=0,
        )
        insert_idx = sum(1 for m in self._messages if m.priority == Priority.PINNED)
        self._messages.insert(insert_idx, summary)

    def snapshot(self) -> list[dict[str, Any]]:
        """Return messages formatted for the Anthropic API (excludes system)."""
        self._reassign_priorities()
        return [{"role": m.role, "content": m.content}
                for m in self._messages if m.role != "system"]

    def system_prompt(self) -> str | None:
        """Extract pinned system messages."""
        parts = [m.content for m in self._messages
                 if m.role == "system" and m.priority == Priority.PINNED]
        return "\n\n".join(parts) if parts else None

    def total_tokens_used(self) -> int:
        return self._total_tokens()

    # -- internals --

    def _reassign_priorities(self) -> None:
        """Reclassify: recent N turns stay RECENT, older become HISTORICAL."""
        non_pinned = [m for m in self._messages if m.priority != Priority.PINNED]
        if len(non_pinned) <= RECENT_TURN_COUNT:
            return
        cutoff = len(non_pinned) - RECENT_TURN_COUNT
        for i, msg in enumerate(non_pinned):
            msg.priority = Priority.HISTORICAL if i < cutoff else Priority.RECENT

    def _total_tokens(self) -> int:
        return sum(m.token_estimate for m in self._messages)

    @staticmethod
    def _estimate_tokens(content: Any) -> int:
        # TODO: replace with proper tokenizer — see memex/active-threads/context-budget-economics.md
        text = content if isinstance(content, str) else str(content)
        return len(text) // 4

    @staticmethod
    def _build_summary_stub(messages: list[TrackedMessage]) -> str:
        """Placeholder for LLM-powered summarization.

        TODO: call Claude to summarize, preserving key decisions,
            file paths, and user constraints.
            See memex/active-threads/context-budget-economics.md
        """
        n = len(messages)
        roles = {}
        for m in messages:
            roles[m.role] = roles.get(m.role, 0) + 1
        role_desc = ", ".join(f"{c} {r}" for r, c in roles.items())
        return (f"[Compacted: {n} messages ({role_desc}) summarized. "
                f"A real implementation calls Claude to preserve key details.]")
