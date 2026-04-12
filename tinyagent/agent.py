"""The agentic loop: Plan -> Act -> Observe -> Reflect.

Runs until the model emits a final text response (no tool calls)
or max_iterations is reached.
"""

from __future__ import annotations
import json
from typing import Any

from tinyagent.client import Client
from tinyagent.context import ContextManager, Priority
from tinyagent.session import Session
from tinyagent.tools import registry

SYSTEM_PROMPT = """\
You are a coding assistant with tools for reading files, writing files,
listing directories, and running shell commands.

Work step by step: understand, explore, plan, implement, verify.
When done, respond with a summary. Do not call tools in your final response."""


class IterationOutcome:
    CONTINUE = "continue"
    DONE = "done"
    ESCALATE = "escalate"


class Agent:
    """Runs the Plan-Act-Observe-Reflect loop."""

    def __init__(self, client: Client, context: ContextManager,
                 session: Session, max_iterations: int = 20) -> None:
        self.client = client
        self.context = context
        self.session = session
        self.max_iterations = max_iterations

    def run(self, task: str) -> str:
        """Start a new task. Returns the final response."""
        self.context.add("system", SYSTEM_PROMPT, Priority.PINNED)
        self.context.add("user", task, Priority.RECENT)
        self.session.record_message("user", task)
        return self._loop()

    def resume(self) -> str:
        """Resume from a saved session."""
        self.context.add("system", SYSTEM_PROMPT, Priority.PINNED)
        for msg in self.session.messages:
            self.context.add(msg["role"], msg["content"])
        return self._loop()

    def _loop(self) -> str:
        for iteration in range(self.max_iterations):
            outcome, text = self._step(iteration)
            if outcome == IterationOutcome.DONE:
                self.session.save()
                return text
            if outcome == IterationOutcome.ESCALATE:
                # TODO: see memex/active-threads/ask-vs-act-thresholds.md
                #   When should the agent ask for clarification instead of
                #   pressing forward? For now we just stop.
                self.session.save()
                return f"[Escalation needed] {text}"
        self.session.save()
        return "[Max iterations reached — stopping.]"

    def _step(self, iteration: int) -> tuple[str, str]:
        """One iteration: send context, parse response, execute tools."""
        messages = self.context.snapshot()
        response = self.client.chat(
            messages=messages,
            tools=registry.get_schemas(),
            system=self.context.system_prompt(),
        )

        # Parse text and tool-use blocks
        text_parts, tool_calls = [], []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({"id": block.id, "name": block.name, "input": block.input})

        assistant_text = "\n".join(text_parts)
        self.context.add("assistant", response.content, Priority.RECENT)
        self.session.record_message("assistant", assistant_text)

        if not tool_calls:
            return IterationOutcome.DONE, assistant_text

        # Execute tools and feed results back
        tool_results = self._execute_tool_calls(tool_calls)
        result_blocks = [{"type": "tool_result", "tool_use_id": tr["id"],
                          "content": tr["output"]} for tr in tool_results]
        self.context.add("user", result_blocks, Priority.RECENT)
        self.session.record_message("tool_results", tool_results)

        # Reflect: detect loops
        # TODO: see memex/active-threads/ask-vs-act-thresholds.md
        #   A real reflect step evaluates progress, detects circles, decides escalation.
        if self._detect_loop():
            return IterationOutcome.ESCALATE, "Possible loop detected."
        return IterationOutcome.CONTINUE, assistant_text

    def _execute_tool_calls(self, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for call in tool_calls:
            try:
                output = registry.execute(call["name"], call["input"])
            except Exception as e:
                output = f"Error executing {call['name']}: {e}"
            results.append({"id": call["id"], "name": call["name"],
                            "input": call["input"], "output": str(output)})
            self.session.record_tool_result(call["id"], call["name"], call["input"], output)
        return results

    def _detect_loop(self) -> bool:
        """If the last 3 tool calls repeat the previous 3, flag it."""
        # TODO: more sophisticated loop detection — see memex/active-threads/ask-vs-act-thresholds.md
        history = self.session.tool_results
        if len(history) < 6:
            return False
        sig = lambda rs: [(r["name"], json.dumps(r["input"], sort_keys=True)) for r in rs]
        return sig(history[-3:]) == sig(history[-6:-3])
