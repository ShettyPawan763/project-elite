"""Scan UTF-8 text files for likely email addresses without exposing matches."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+")
_DEFAULT_MAX_BYTES = 1_000_000


@dataclass(frozen=True)
class Finding:
    """A location and category only; never retain the matched sensitive value."""

    path: Path
    line: int
    kind: str = "possible email address"


def _text_files(root: Path, max_bytes: int) -> Iterator[Path]:
    """Yield regular, non-symlink files small enough to inspect."""
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(directory)
        dirnames[:] = [name for name in dirnames if not (current / name).is_symlink()]
        for filename in filenames:
            candidate = current / filename
            try:
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                if candidate.stat().st_size > max_bytes:
                    continue
            except OSError:
                continue
            yield candidate


def scan_directory(directory: str | Path, *, max_bytes: int = _DEFAULT_MAX_BYTES) -> list[Finding]:
    """Return possible email locations under *directory*.

    Binary files, symlinks, and files larger than ``max_bytes`` are skipped.
    File contents and matched values are never included in findings.
    """
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")

    findings: list[Finding] = []
    for path in _text_files(root, max_bytes):
        try:
            with path.open("rb") as source:
                data = source.read(max_bytes + 1)
            if len(data) > max_bytes or b"\0" in data[:8192]:
                continue
            text = data.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            if _EMAIL.search(line):
                findings.append(Finding(path=path.relative_to(root), line=line_number))
    return findings
