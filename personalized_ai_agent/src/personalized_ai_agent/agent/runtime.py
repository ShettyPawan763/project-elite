"""Layered agent runtime: model, policy, skill approval, and skill execution."""

from __future__ import annotations

import json
from typing import Any, Callable

from personalized_ai_agent.behaviour.policy import confirm_action
from personalized_ai_agent.connectors.openai_compatible import complete
from personalized_ai_agent.skills import task_management

MAX_ACTION_ROUNDS = 5


def _handle_tool_call(
    call: object,
    approve: Callable[[str, dict[str, object]], bool],
) -> tuple[str, str]:
    if not isinstance(call, dict):
        raise ValueError("The AI provider returned an invalid tool call.")
    call_id = call.get("id")
    function = call.get("function")
    if not isinstance(call_id, str) or not isinstance(function, dict):
        raise ValueError("The AI provider returned an invalid tool call.")
    name = function.get("name")
    raw_arguments = function.get("arguments", "{}")
    if not isinstance(name, str) or not isinstance(raw_arguments, str):
        raise ValueError("The AI provider returned invalid tool arguments.")
    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError as error:
        raise ValueError("The AI provider returned malformed tool arguments.") from error
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object.")

    if task_management.requires_confirmation(name) and not approve(name, arguments):
        return call_id, json.dumps({"ok": False, "message": "User declined this action."})
    try:
        result = task_management.execute(name, arguments)
    except (OSError, ValueError) as error:
        return call_id, json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)
    return call_id, json.dumps({"ok": True, "result": result}, ensure_ascii=False)


def run_turn(
    messages: list[dict[str, Any]],
    approve: Callable[[str, dict[str, object]], bool] = confirm_action,
) -> str:
    """Run one user turn, including bounded tool calls, and return the final answer."""
    for _ in range(MAX_ACTION_ROUNDS):
        message = complete(messages, task_management.definitions())
        messages.append(message)
        tool_calls = message.get("tool_calls")
        if not tool_calls:
            answer = message.get("content")
            return answer if isinstance(answer, str) else "The assistant returned no text."
        if not isinstance(tool_calls, list):
            raise ValueError("AI provider returned invalid tool calls.")
        for call in tool_calls:
            call_id, content = _handle_tool_call(call, approve)
            messages.append({"role": "tool", "tool_call_id": call_id, "content": content})
    return "I reached the action limit for this request. Please try a simpler task."
