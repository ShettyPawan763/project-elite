"""Local-only checks for likely sensitive data."""

from .scanner import Finding, scan_directory

__all__ = ["Finding", "scan_directory"]
