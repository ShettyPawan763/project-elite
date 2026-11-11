# Project Elite

A portfolio of projects made and updated weekly or yearly.

## Projects

- **Local Privacy Scanner:** scans small local text files for likely personal data and credential patterns. See the scanner usage below.
- **Personalized AI Agent:** a local-profile, session-based chat assistant. See [personalized_ai_agent/README.md](personalized_ai_agent/README.md) for setup, provider configuration, and privacy details.

## Local Privacy Scanner

The scanner checks small UTF-8 text files for possible email addresses, recognizable GitHub tokens, AWS access key IDs, and credential assignments.

## Install

```sh
python -m pip install -e .
```

## Use

```sh
privacy-scan ./folder-to-check
```

Skip paths with repeatable relative glob patterns:

```sh
privacy-scan ./folder-to-check --exclude 'build/**' --exclude '*.log'
```

The report contains a relative file path, line number, and finding type. It never prints the matched value or a line of file contents. The scanner skips excluded paths, symlinks, binary files, unreadable or non-UTF-8 files, and files larger than 1 MB.

The scan runs locally and does not make network requests. Pattern matching is heuristic: it can miss sensitive values and may flag harmless text. The scanner does not validate credentials with their providers. A clean scan is not proof that a folder contains no sensitive information.

## Development

```sh
python -m unittest discover -s tests
```
