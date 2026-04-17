"""Row-backed model base — exposes sqlite3.Row columns as attributes.

Subclasses wrap a single DB row and add methods that query related data.
This keeps raw `row['col']` subscript access out of routes and templates
while still letting Jinja use `{{ team.name }}` unchanged.
"""
from __future__ import annotations

import sqlite3
from typing import Any


class RowModel:
    """Base class for models backed by a single sqlite3.Row.

    Attribute access falls through to the row's columns, so
    `team.short_name` returns `row['short_name']`. Subclasses override
    `__init__` to add derived fields and `__slots__` for clarity.
    """

    __slots__ = ("_row",)

    def __init__(self, row: sqlite3.Row) -> None:
        self._row = row

    def __getattr__(self, name: str) -> Any:
        # Called only when normal attribute lookup fails.
        try:
            return self._row[name]
        except (IndexError, KeyError) as e:
            raise AttributeError(
                f"{type(self).__name__} has no attribute or column {name!r}"
            ) from e

    def __getitem__(self, key: str) -> Any:
        # Templates and callers that used dict-style access keep working.
        return self._row[key]

    def __contains__(self, key: str) -> bool:
        return key in self._row.keys()

    def keys(self) -> list[str]:
        return list(self._row.keys())

    @property
    def row(self) -> sqlite3.Row:
        """Escape hatch — return the underlying row if a caller needs it."""
        return self._row

    def __repr__(self) -> str:
        pk = getattr(self, "id", "?")
        return f"<{type(self).__name__} id={pk}>"
