"""Newspaper edition persistence."""
from __future__ import annotations

import json
from typing import Any

from db import get_db

EDITION_WEEKS = {1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24}
INTERVIEW_HOSTS = {1: 1, 2: 2, 3: 3, 4: 1, 5: 2, 6: 3}


def _ensure_table() -> None:
    get_db().execute("""
        CREATE TABLE IF NOT EXISTS newspaper_editions (
            id INTEGER PRIMARY KEY,
            edition_num INTEGER UNIQUE NOT NULL,
            week_num INTEGER NOT NULL,
            headline TEXT NOT NULL,
            subheadline TEXT,
            articles TEXT NOT NULL,
            interview TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)


def save_edition(
    edition_num: int,
    week_num: int,
    headline: str,
    subheadline: str,
    articles: list[dict[str, Any]],
    interview: dict[str, Any],
) -> None:
    """Upsert a newspaper edition."""
    _ensure_table()
    db = get_db()
    db.execute("""
        INSERT INTO newspaper_editions
            (edition_num, week_num, headline, subheadline, articles, interview)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(edition_num) DO UPDATE SET
            week_num=excluded.week_num, headline=excluded.headline,
            subheadline=excluded.subheadline, articles=excluded.articles,
            interview=excluded.interview
    """, (edition_num, week_num, headline, subheadline,
          json.dumps(articles, ensure_ascii=False),
          json.dumps(interview, ensure_ascii=False)))
    db.commit()


def get_edition(edition_num: int) -> dict[str, Any] | None:
    """Fetch a single edition with parsed JSON fields."""
    _ensure_table()
    row = get_db().execute(
        "SELECT * FROM newspaper_editions WHERE edition_num=?",
        (edition_num,),
    ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["articles"] = json.loads(d["articles"])
    d["interview"] = json.loads(d["interview"])
    return d


def get_all_editions() -> list[dict[str, Any]]:
    """All editions (without parsing heavy JSON — just metadata)."""
    _ensure_table()
    rows = get_db().execute(
        "SELECT edition_num, week_num, headline, subheadline, created_at "
        "FROM newspaper_editions ORDER BY edition_num"
    ).fetchall()
    return [dict(r) for r in rows]
