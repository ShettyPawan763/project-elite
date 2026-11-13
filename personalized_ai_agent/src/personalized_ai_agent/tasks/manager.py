"""Validated persistence operations for the local task list."""

from __future__ import annotations

import json
import os
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_TASKS = Path.home() / ".personalized-ai-agent" / "tasks.json"


def tasks_path() -> Path:
    return Path(os.environ.get("AI_AGENT_TASKS", DEFAULT_TASKS)).expanduser()


def _load_tasks(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read task list: {error}") from error
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise ValueError("Task list must be a JSON array of task objects.")
    return data


def _save_tasks(path: Path, tasks: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        temporary.chmod(0o600)
    except OSError:
        pass
    temporary.replace(path)


def list_tasks() -> dict[str, Any]:
    tasks = _load_tasks(tasks_path())
    return {"tasks": tasks, "count": len(tasks)}


def add_task(title: object, due_date: object) -> dict[str, Any]:
    if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
        raise ValueError("Task title must contain 1 to 200 characters.")
    if due_date is not None:
        if not isinstance(due_date, str):
            raise ValueError("Due date must be YYYY-MM-DD or null.")
        try:
            due_date = date.fromisoformat(due_date).isoformat()
        except ValueError as error:
            raise ValueError("Due date must be a valid YYYY-MM-DD date.") from error

    path = tasks_path()
    tasks = _load_tasks(path)
    if len(tasks) >= 500:
        raise ValueError("Task list is full (500 tasks).")
    task = {
        "id": uuid.uuid4().hex[:8],
        "title": title.strip(),
        "due_date": due_date,
        "completed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    tasks.append(task)
    _save_tasks(path, tasks)
    return {"task": task}


def complete_task(task_id: object) -> dict[str, Any]:
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("Task ID is required.")
    path = tasks_path()
    tasks = _load_tasks(path)
    for task in tasks:
        if task.get("id") == task_id.strip():
            if task.get("completed") is True:
                return {"task": task, "already_completed": True}
            task["completed"] = True
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            _save_tasks(path, tasks)
            return {"task": task}
    raise ValueError(f"No task found with ID {task_id!r}.")
