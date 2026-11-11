"""Command-line interface for the local privacy scanner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .scanner import scan_directory


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="privacy-scan",
        description="Scan a folder locally for possible personal data and credentials.",
    )
    parser.add_argument("directory", type=Path, help="folder to scan")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="skip matching relative paths (repeatable, e.g. --exclude 'build/**')",
    )
    args = parser.parse_args()

    try:
        findings = scan_directory(args.directory, exclude=args.exclude)
    except (NotADirectoryError, ValueError) as error:
        print(f"privacy-scan: {error}", file=sys.stderr)
        return 2

    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.kind}")
    print(f"Scan complete: {len(findings)} possible finding(s).")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
