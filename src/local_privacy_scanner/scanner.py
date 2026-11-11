"""Scan UTF-8 text files for likely sensitive values without exposing matches."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Iterable, Iterator

_DETECTORS = (
    (
        "possible email address",
        re.compile(
            r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+"
        ),
    ),
    ("possible GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("possible AWS access key ID", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    (
        "possible credential assignment",
        re.compile(
            r"\b(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9/+_=-]{12,}['\"]?",
            re.IGNORECASE,
        ),
    ),
)
_DEFAULT_MAX_BYTES = 1_000_000


@dataclass(frozen=True)
class Finding:
    """A location and category only; never retain the matched sensitive value."""

    path: Path
    line: int
    kind: str = "possible email address"


def _matches_exclusion(relative_path: str, patterns: tuple[str, ...]) -> bool:
    path = PurePosixPath(relative_path)
    return any(path.match(pattern) for pattern in patterns)


def _normalize_exclusions(patterns: Iterable[str]) -> tuple[str, ...]:
    normalized = []
    for pattern in patterns:
        normalized_pattern = pattern.replace("\\", "/")
        if (
            not normalized_pattern
            or PurePosixPath(normalized_pattern).is_absolute()
            or PureWindowsPath(pattern).is_absolute()
            or ".." in PurePosixPath(normalized_pattern).parts
        ):
            raise ValueError("exclude patterns must be non-empty relative paths without '..'")
        normalized.append(normalized_pattern)
    return tuple(normalized)


def _text_files(root: Path, max_bytes: int, exclusions: tuple[str, ...]) -> Iterator[Path]:
    """Yield regular, non-symlink files small enough to inspect."""
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(directory)
        dirnames[:] = [
            name
            for name in dirnames
            if not (current / name).is_symlink()
            and not _matches_exclusion(
                (current / name).relative_to(root).as_posix(), exclusions
            )
        ]
        for filename in filenames:
            candidate = current / filename
            try:
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                if _matches_exclusion(candidate.relative_to(root).as_posix(), exclusions):
                    continue
                if candidate.stat().st_size > max_bytes:
                    continue
            except OSError:
                continue
            yield candidate


def scan_directory(
    directory: str | Path,
    *,
    max_bytes: int = _DEFAULT_MAX_BYTES,
    exclude: Iterable[str] = (),
) -> list[Finding]:
    """Return locations of possible sensitive data under *directory*.

    Binary files, symlinks, excluded paths, and files larger than ``max_bytes`` are skipped.
    Exclusion patterns use relative, slash-separated glob paths.
    File contents and matched values are never included in findings.
    """
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    exclusions = _normalize_exclusions(exclude)

    findings: list[Finding] = []
    for path in _text_files(root, max_bytes, exclusions):
        try:
            with path.open("rb") as source:
                data = source.read(max_bytes + 1)
            if len(data) > max_bytes or b"\0" in data[:8192]:
                continue
            text = data.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            for kind, pattern in _DETECTORS:
                if pattern.search(line):
                    findings.append(Finding(path=path.relative_to(root), line=line_number, kind=kind))
    return findings
