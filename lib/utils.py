"""Shared utility functions."""
from __future__ import annotations


def format_ip(outs: int | None) -> str:
    """Convert total outs to innings pitched display (e.g., 19 outs = 6.1)."""
    if not outs:
        return "0.0"
    innings = outs // 3
    remainder = outs % 3
    return f"{innings}.{remainder}"
