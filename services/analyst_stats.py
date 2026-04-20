"""Analyst pick accuracy stats — per-team, streaks, weekly trends."""
from __future__ import annotations

from typing import Any

from db import get_db


def get_pick_accuracy_by_team(analyst_id: int) -> list[dict[str, Any]]:
    """Per-team pick accuracy for one analyst.

    Returns list sorted by total desc:
        [{team_id, short_name, color_primary, logo_file, correct, total, pct}]
    """
    db = get_db()
    rows = db.execute("""
        WITH picks AS (
            SELECT p.picked_team_id,
                   s.home_team_id, s.away_team_id,
                   CASE
                       WHEN (s.home_team_id = p.picked_team_id AND g.home_runs > g.away_runs)
                         OR (s.away_team_id = p.picked_team_id AND g.away_runs > g.home_runs)
                       THEN 1 ELSE 0
                   END AS correct
            FROM analyst_game_picks p
            JOIN schedule s ON p.schedule_id = s.id
            JOIN games g ON g.schedule_id = s.id
            WHERE p.analyst_id = ?
        ),
        team_picks AS (
            SELECT home_team_id AS team_id, correct FROM picks
            UNION ALL
            SELECT away_team_id AS team_id, correct FROM picks
        )
        SELECT tp.team_id, t.short_name, t.color_primary, t.logo_file,
               SUM(tp.correct) AS correct, COUNT(*) AS total
        FROM team_picks tp
        JOIN teams t ON tp.team_id = t.id
        GROUP BY tp.team_id
        ORDER BY total DESC
    """, (analyst_id,)).fetchall()
    return [
        {**dict(r), "pct": round(r["correct"] / r["total"] * 100, 1) if r["total"] else 0}
        for r in rows
    ]


def get_pick_streaks(analyst_id: int) -> dict[str, Any]:
    """Current and longest win/loss streaks for an analyst's picks.

    Returns {current_type, current_length, longest_w, longest_l}.
    """
    db = get_db()
    rows = db.execute("""
        SELECT
            CASE
                WHEN (s.home_team_id = p.picked_team_id AND g.home_runs > g.away_runs)
                  OR (s.away_team_id = p.picked_team_id AND g.away_runs > g.home_runs)
                THEN 1 ELSE 0
            END AS correct
        FROM analyst_game_picks p
        JOIN schedule s ON p.schedule_id = s.id
        JOIN games g ON g.schedule_id = s.id
        WHERE p.analyst_id = ?
        ORDER BY s.game_num
    """, (analyst_id,)).fetchall()

    current_type = '-'
    current_len = 0
    longest_w = 0
    longest_l = 0
    for r in rows:
        c = 'W' if r['correct'] else 'L'
        if c == current_type:
            current_len += 1
        else:
            current_type = c
            current_len = 1
        if c == 'W':
            longest_w = max(longest_w, current_len)
        else:
            longest_l = max(longest_l, current_len)
    return {
        "current_type": current_type,
        "current_length": current_len,
        "longest_w": longest_w,
        "longest_l": longest_l,
    }


def get_weekly_accuracy(analyst_id: int) -> list[dict[str, Any]]:
    """Per-week pick accuracy for sparkline trend.

    Returns list sorted by week_num ascending:
        [{week_num, correct, total, pct}]
    """
    db = get_db()
    rows = db.execute("""
        SELECT p.week_num,
               COUNT(*) AS total,
               SUM(CASE
                   WHEN (s.home_team_id = p.picked_team_id AND g.home_runs > g.away_runs)
                     OR (s.away_team_id = p.picked_team_id AND g.away_runs > g.home_runs)
                   THEN 1 ELSE 0
               END) AS correct
        FROM analyst_game_picks p
        JOIN schedule s ON p.schedule_id = s.id
        JOIN games g ON g.schedule_id = s.id
        WHERE p.analyst_id = ?
        GROUP BY p.week_num
        ORDER BY p.week_num
    """, (analyst_id,)).fetchall()
    return [
        {**dict(r), "pct": round(r["correct"] / r["total"] * 100, 1) if r["total"] else 0}
        for r in rows
    ]
