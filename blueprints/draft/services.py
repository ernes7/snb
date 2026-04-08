"""Draft blueprint services."""
from __future__ import annotations

import sqlite3

from db import get_db


def get_draft_picks() -> list[sqlite3.Row]:
    """Get all draft picks with team and player info."""
    return get_db().execute("""
        SELECT dp.*, t.name as team_name, t.short_name, t.owner, t.color_primary,
            t.rank_pre_draft, t.rank_post_draft, t.logo_file,
            p.name as player_name, p.id as player_id, p.position as player_position
        FROM draft_picks dp
        JOIN teams t ON dp.team_id = t.id
        LEFT JOIN players p ON dp.player_id = p.id
        ORDER BY dp.pick_num
    """).fetchall()


def get_draft_teams() -> list[sqlite3.Row]:
    """Get teams ordered by pre-draft ranking."""
    return get_db().execute(
        "SELECT * FROM teams ORDER BY rank_pre_draft DESC"
    ).fetchall()
