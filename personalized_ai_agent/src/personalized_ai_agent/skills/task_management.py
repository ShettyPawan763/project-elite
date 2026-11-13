"""Task-management skill definitions and allowlisted dispatch."""

from __future__ import annotations

from typing import Any

from personalized_ai_agent.tasks import manager

TASK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "todo_list",
            "description": "List the user's saved tasks and their IDs/statuses.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "todo_add",
            "description": "Add a task to the user's local task list. Ask for confirmation before running.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short task title"},
                    "due_date": {"type": ["string", "null"], "description": "Optional due date in YYYY-MM-DD format"},
                },
                "required": ["title", "due_date"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "todo_complete",
            "description": "Mark an existing task complete using its task ID. Ask for confirmation before running.",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "string", "description": "ID returned by todo_list"}},
                "required": ["task_id"],
                "additionalProperties": False,
            },
        },
    },
]

_MUTATING_SKILLS = {"todo_add", "todo_complete"}


def definitions() -> list[dict[str, Any]]:
    return TASK_TOOLS


def requires_confirmation(name: str) -> bool:
    return name in _MUTATING_SKILLS


def execute(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object.")
    if name == "todo_list":
        if arguments:
            raise ValueError("todo_list takes no arguments.")
        return manager.list_tasks()
    if name == "todo_add":
        if set(arguments) != {"title", "due_date"}:
            raise ValueError("todo_add requires only title and due_date.")
        return manager.add_task(arguments["title"], arguments["due_date"])
    if name == "todo_complete":
        if set(arguments) != {"task_id"}:
            raise ValueError("todo_complete requires only task_id.")
        return manager.complete_task(arguments["task_id"])
    raise ValueError(f"Skill {name!r} is not available.")
