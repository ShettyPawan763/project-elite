"""Backward-compatible exports for the original task-tool module."""

from personalized_ai_agent.skills.task_management import TASK_TOOLS, execute, requires_confirmation

run_tool = execute

__all__ = ["TASK_TOOLS", "requires_confirmation", "run_tool"]
