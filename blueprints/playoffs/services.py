"""Playoffs blueprint services."""
from __future__ import annotations

import sqlite3

from db import get_db


def get_series(phase: str) -> list[sqlite3.Row]:
    """Get all games for a playoff series phase."""
    return get_db().execute("""
        SELECT s.*, g.home_runs, g.away_runs, g.date, g.id as game_id,
            ht.name as home_name, ht.short_name as home_short,
            ht.color_primary as home_color, ht.logo_file as home_logo,
            at.name as away_name, at.short_name as away_short,
            at.color_primary as away_color, at.logo_file as away_logo,
            wp.name as wp_name
        FROM schedule s
        LEFT JOIN teams ht ON s.home_team_id = ht.id
        LEFT JOIN teams at ON s.away_team_id = at.id
        LEFT JOIN games g ON g.schedule_id = s.id
        LEFT JOIN players wp ON g.winning_pitcher_id = wp.id
        WHERE s.phase = ?
        ORDER BY s.series_game
    """, (phase,)).fetchall()
