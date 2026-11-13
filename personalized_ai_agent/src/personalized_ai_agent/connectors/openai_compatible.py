"""Connector for OpenAI-compatible chat completions APIs."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def complete(messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY before starting a chat.")

    base_url = os.environ.get("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("AI_MODEL", "gpt-4o-mini")
    body = json.dumps(
        {"model": model, "messages": messages, "tools": tools, "tool_choice": "auto"}
    ).encode("utf-8")
    request = Request(
        f"{base_url}/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read(500).decode("utf-8", errors="replace")
        raise ValueError(f"AI provider returned HTTP {error.code}: {detail}") from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not reach the AI provider: {error}") from error

    try:
        message = result["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("AI provider returned an unexpected response.") from error
    if not isinstance(message, dict):
        raise ValueError("AI provider returned an unexpected message.")
    return message
