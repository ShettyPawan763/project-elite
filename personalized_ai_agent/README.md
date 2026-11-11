# Personalized AI Agent

A small, local-first command-line assistant that adapts its answers to a profile you control.

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

## Chat

```sh
# macOS/Linux
export OPENAI_API_KEY="your-key"

# PowerShell
$env:OPENAI_API_KEY = "your-key"

personal-agent chat
```

Type `/reset` to clear the current conversation or `/quit` to exit. Conversation history exists only for the current process and is not written to disk.

## Privacy

The profile and conversation are included in requests to the configured chat completions API so the model can personalize its answers. They are sent over HTTPS when using the default OpenAI endpoint. The profile is stored locally as plain text; protect the file like other personal notes. This tool does not collect telemetry, and it does not claim that profile data is encrypted at rest. Review your provider's data handling terms before use.

The agent only replies in chat. It cannot run shell commands, browse the web, or take actions on your behalf.

## Configuration

- `OPENAI_API_KEY`: required API key
- `AI_BASE_URL`: API root, defaults to `https://api.openai.com/v1`
- `AI_MODEL`: model name, defaults to `gpt-4o-mini`
- `AI_AGENT_PROFILE`: optional profile JSON path
