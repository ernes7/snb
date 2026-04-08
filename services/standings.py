"""Shared standings service — used by main, teams, and playoffs."""
from __future__ import annotations

import sqlite3
from typing import Any

from db import get_db


def get_standings() -> list[dict[str, Any]]:
    """Compute league standings from game results."""
    db = get_db()
    teams = db.execute("SELECT * FROM teams").fetchall()
    standings: list[dict[str, Any]] = []

    for t in teams:
        row = dict(t)
        stats = db.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN (s.home_team_id=:tid AND g.home_runs>g.away_runs) OR
                    (s.away_team_id=:tid AND g.away_runs>g.home_runs) THEN 1 ELSE 0 END), 0) as wins,
                COALESCE(SUM(CASE WHEN (s.home_team_id=:tid AND g.home_runs<g.away_runs) OR
                    (s.away_team_id=:tid AND g.away_runs<g.home_runs) THEN 1 ELSE 0 END), 0) as losses,
                COALESCE(SUM(CASE WHEN s.home_team_id=:tid THEN g.home_runs
                    WHEN s.away_team_id=:tid THEN g.away_runs ELSE 0 END), 0) as rs,
                COALESCE(SUM(CASE WHEN s.home_team_id=:tid THEN g.away_runs
                    WHEN s.away_team_id=:tid THEN g.home_runs ELSE 0 END), 0) as ra
            FROM games g JOIN schedule s ON g.schedule_id=s.id
            WHERE s.phase='regular' AND (s.home_team_id=:tid OR s.away_team_id=:tid)
        """, {"tid": t['id']}).fetchone()

        row['wins'] = stats['wins']
        row['losses'] = stats['losses']
        total = stats['wins'] + stats['losses']
        row['pct'] = f"{stats['wins']/total:.3f}" if total > 0 else ".000"
        row['rs'] = stats['rs']
        row['ra'] = stats['ra']
        row['diff'] = stats['rs'] - stats['ra']
        standings.append(row)

    standings.sort(key=lambda x: (-x['wins'], x['losses']))

    if standings and (standings[0]['wins'] + standings[0]['losses']) > 0:
        top = standings[0]['wins'] - standings[0]['losses']
        for s in standings:
            diff = top - (s['wins'] - s['losses'])
            s['gb'] = '-' if diff == 0 else f"{diff/2:.1f}"
    else:
        for s in standings:
            s['gb'] = '-'

    return standings


def get_all_teams() -> list[sqlite3.Row]:
    """Get all teams ordered by name."""
    return get_db().execute("SELECT * FROM teams ORDER BY name").fetchall()
