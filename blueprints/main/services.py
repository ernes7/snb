"""Main blueprint services."""
from __future__ import annotations

import sqlite3

from db import get_db


def get_recent_games(limit: int = 10) -> list[sqlite3.Row]:
    """Get the most recent game results."""
    return get_db().execute("""
        SELECT g.*, s.game_num, s.phase,
            ht.name as home_name, ht.short_name as home_short, ht.owner as home_owner,
            ht.color_primary as home_color, ht.logo_file as home_logo,
            at.name as away_name, at.short_name as away_short, at.owner as away_owner,
            at.color_primary as away_color, at.logo_file as away_logo,
            wp.name as wp_name, lp.name as lp_name, sp.name as sp_name
        FROM games g
        JOIN schedule s ON g.schedule_id = s.id
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        LEFT JOIN players wp ON g.winning_pitcher_id = wp.id
        LEFT JOIN players lp ON g.losing_pitcher_id = lp.id
        LEFT JOIN players sp ON g.save_pitcher_id = sp.id
        ORDER BY g.id DESC LIMIT ?
    """, (limit,)).fetchall()
