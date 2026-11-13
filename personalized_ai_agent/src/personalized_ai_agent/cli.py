"""Command-line interface for the personalized AI agent."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from personalized_ai_agent.agent.runtime import run_turn
from personalized_ai_agent.behaviour.policy import system_message

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


def chat(profile: dict[str, str]) -> None:
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_message(profile)}]
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
            print(f"Agent: {run_turn(messages)}")
        except ValueError as error:
            print(f"personal-agent: {error}", file=sys.stderr)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="personal-agent", description="Your profile-aware AI assistant.")
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
