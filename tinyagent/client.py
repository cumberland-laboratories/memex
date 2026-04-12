"""Thin Anthropic SDK wrapper. Only responsibility: send messages, retry on 429."""

from __future__ import annotations
import time
from typing import Any, Iterator
import anthropic

MAX_RETRIES = 3
INITIAL_BACKOFF_S = 1.0


class Client:
    """Minimal Anthropic API client with rate-limit retry."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> anthropic.types.Message:
        """Send a chat request. Retries on rate-limit with exponential backoff."""
        return self._call_with_retry(
            lambda: self._client.messages.create(
                **self._build_kwargs(messages, tools, system, max_tokens)))

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> Iterator[Any]:
        """Stream a chat response. Same retry logic on initial connection."""
        kwargs = self._build_kwargs(messages, tools, system, max_tokens)
        kwargs["stream"] = True
        return self._call_with_retry(
            lambda: self._client.messages.create(**kwargs))

    def _build_kwargs(self, messages, tools, system, max_tokens) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.model, "messages": messages, "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
        if system:
            kwargs["system"] = system
        return kwargs

    def _call_with_retry(self, fn):
        backoff = INITIAL_BACKOFF_S
        for attempt in range(MAX_RETRIES + 1):
            try:
                return fn()
            except anthropic.RateLimitError:
                if attempt == MAX_RETRIES:
                    raise
                time.sleep(backoff)
                backoff *= 2
