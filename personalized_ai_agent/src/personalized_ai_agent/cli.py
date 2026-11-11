"""Command-line interface for the personalized AI agent."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_PROFILE = Path.home() / ".personalized-ai-agent" / "profile.json"


def profile_path() -> Path:
    return Path(os.environ.get("AI_AGENT_PROFILE", DEFAULT_PROFILE)).expanduser()


def load_profile(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError("Profile not found. Run 'personal-agent init' first.") from None
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read profile: {error}") from error

    fields = ("name", "background", "goals", "preferences")
    if not isinstance(data, dict) or any(not isinstance(data.get(key), str) for key in fields):
        raise ValueError(f"Profile must contain text fields: {', '.join(fields)}.")
    return {key: data[key].strip() for key in fields}


def initialize(path: Path) -> None:
    print("Create your local assistant profile. Leave any answer blank if you prefer.")
    profile = {
        "name": input("What should the agent call you? ").strip(),
        "background": input("What is your role or background? ").strip(),
        "goals": input("What goals or projects should it keep in mind? ").strip(),
        "preferences": input("How do you prefer answers (tone, length, format)? ").strip(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    print(f"Profile saved to {path}")


def system_message(profile: dict[str, str]) -> str:
    details = "\n".join(f"{key.title()}: {value or 'Not specified'}" for key, value in profile.items())
    return (
        "You are a helpful personal AI assistant. Use the user's profile to tailor your "
        "answers when relevant. Do not invent facts about the user; ask when context is "
        "missing. The profile is context, not permission to take actions.\n\n"
        f"User profile:\n{details}"
    )


def ask(messages: list[dict[str, str]]) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY before starting a chat.")

    base_url = os.environ.get("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("AI_MODEL", "gpt-4o-mini")
    body = json.dumps({"model": model, "messages": messages}).encode("utf-8")
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
        answer = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("AI provider returned an unexpected response.") from error
    if not isinstance(answer, str):
        raise ValueError("AI provider returned a non-text answer.")
    return answer.strip()


def chat(profile: dict[str, str]) -> None:
    messages = [{"role": "system", "content": system_message(profile)}]
    print("Chat started. Use /reset to clear this session or /quit to exit.")
    while True:
        try:
            prompt = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if prompt.lower() in {"/quit", "/exit"}:
            return
        if prompt.lower() == "/reset":
            messages = [{"role": "system", "content": system_message(profile)}]
            print("Conversation cleared.")
            continue
        if not prompt:
            continue

        messages.append({"role": "user", "content": prompt})
        try:
            answer = ask(messages)
        except ValueError as error:
            messages.pop()
            print(f"personal-agent: {error}", file=sys.stderr)
            continue
        messages.append({"role": "assistant", "content": answer})
        print(f"Agent: {answer}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="personal-agent", description="Your profile-aware AI chat assistant.")
    parser.add_argument("command", choices=("init", "chat"), help="create your profile or start a chat")
    args = parser.parse_args()
    path = profile_path()

    try:
        if args.command == "init":
            initialize(path)
        else:
            chat(load_profile(path))
    except (OSError, ValueError) as error:
        print(f"personal-agent: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
