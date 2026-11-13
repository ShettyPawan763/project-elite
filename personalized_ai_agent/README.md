# Personalized AI Agent

A small, local-first command-line assistant that adapts its answers to a profile you control and can manage a local task list with your approval.

## Architecture

The assistant is organized as a stack of small layers:

- `agent/`: orchestrates model turns and bounds the tool-action loop.
- `behaviour/`: defines the assistant's rules and asks before actions that change data.
- `skills/`: exposes the allowlisted capabilities the model can request.
- `tasks/`: validates and stores the local task list.
- `connectors/`: communicates with the configured AI provider.
- `cli.py`: handles profile setup and the terminal conversation.

Each layer has a narrow job. New skills and service connectors can be added without putting their implementation into the CLI.

## Requirements

- Python 3.10+
- An OpenAI-compatible chat completions API key
- Optional: set `AI_BASE_URL` and `AI_MODEL` for a compatible provider or model

## Install

From this directory:

```sh
python -m pip install -e .
```

## Set up your profile

```sh
personal-agent init
```

The setup asks for your name, role or background, goals, and response preferences. It saves these fields as readable JSON at `~/.personalized-ai-agent/profile.json` (or the path in `AI_AGENT_PROFILE`). You can edit or delete that file at any time.

## Chat and task actions

Set the API key, then start a chat:

```sh
# macOS/Linux
export OPENAI_API_KEY="your-key"

# PowerShell
$env:OPENAI_API_KEY = "your-key"

personal-agent chat
```

The assistant can list your saved tasks, add a task with an optional due date, and mark a task complete. It asks before adding or completing tasks; listing tasks is read-only. Try requests such as "What tasks do I have?" or "Add prepare the project demo for Friday." Use `/reset` to clear the current conversation or `/quit` to exit.

Tasks are stored locally as JSON at `~/.personalized-ai-agent/tasks.json` (or the path in `AI_AGENT_TASKS`). The model must return a task ID from the list before a task can be marked complete.

## Privacy and action limits

The profile and conversation are sent to the configured chat completions API so the model can personalize its answers and select task tools. Task data remains in a local JSON file and is included in a provider request only when needed for a task action. The profile and task files are plain text; protect them like other personal notes. This tool does not collect telemetry. Review your provider's data handling terms before use.

The assistant can only use the built-in task actions. It cannot send email, access a calendar, browse the web, or run shell commands. Mutating task actions require an explicit confirmation in the terminal. Declined actions are not run.

## Configuration

- `OPENAI_API_KEY`: required API key
- `AI_BASE_URL`: API root, defaults to `https://api.openai.com/v1`
- `AI_MODEL`: model name, defaults to `gpt-4o-mini`
- `AI_AGENT_PROFILE`: optional profile JSON path
- `AI_AGENT_TASKS`: optional local task-list JSON path
