"""Games blueprint services."""
from __future__ import annotations

from typing import Any

from db import get_db


def get_game_form_data(schedule_id: int) -> dict[str, Any] | None:
    """Get all data needed for the game entry form."""
    db = get_db()
    sched = db.execute("""
        SELECT s.*, ht.name as home_name, ht.short_name as home_short,
            ht.color_primary as home_color,
            at.name as away_name, at.short_name as away_short,
            at.color_primary as away_color
        FROM schedule s
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        WHERE s.id = ?
    """, (schedule_id,)).fetchone()

    if not sched:
        return None

    home_pitchers = db.execute("""
        SELECT id, name FROM players WHERE team_id=? AND role IN ('rotation','bullpen')
        ORDER BY role, lineup_order
    """, (sched['home_team_id'],)).fetchall()

    away_pitchers = db.execute("""
        SELECT id, name FROM players WHERE team_id=? AND role IN ('rotation','bullpen')
        ORDER BY role, lineup_order
    """, (sched['away_team_id'],)).fetchall()

    existing = db.execute(
        "SELECT * FROM games WHERE schedule_id=?", (schedule_id,)
    ).fetchone()

    return {
        'sched': sched,
        'game': existing,
        'home_pitchers': home_pitchers,
        'away_pitchers': away_pitchers,
    }


def save_game(form: ImmutableMultiDict[str, str]) -> int:
    """Save or update a game result. Returns the game ID."""
    schedule_id = int(form['schedule_id'])
    db = get_db()
    existing = db.execute(
        "SELECT id FROM games WHERE schedule_id=?", (schedule_id,)
    ).fetchone()

    wp_id = int(form['winning_pitcher_id']) if form.get('winning_pitcher_id') else None
    lp_id = int(form['losing_pitcher_id']) if form.get('losing_pitcher_id') else None
    sv_id = int(form['save_pitcher_id']) if form.get('save_pitcher_id') else None

    vals = (
        form.get('date', ''),
        int(form['home_runs']) if form.get('home_runs') else 0,
        int(form['away_runs']) if form.get('away_runs') else 0,
        int(form['home_hits']) if form.get('home_hits') else 0,
        int(form['away_hits']) if form.get('away_hits') else 0,
        int(form['home_errors']) if form.get('home_errors') else 0,
        int(form['away_errors']) if form.get('away_errors') else 0,
        wp_id, lp_id, sv_id,
        form.get('notes', ''),
    )

    if existing:
        db.execute("""
            UPDATE games SET date=?, home_runs=?, away_runs=?, home_hits=?, away_hits=?,
                home_errors=?, away_errors=?, winning_pitcher_id=?, losing_pitcher_id=?,
                save_pitcher_id=?, notes=?
            WHERE schedule_id=?
        """, vals + (schedule_id,))
        db.commit()
        return existing['id']
    else:
        cursor = db.execute("""
            INSERT INTO games (schedule_id, date, home_runs, away_runs, home_hits, away_hits,
                home_errors, away_errors, winning_pitcher_id, losing_pitcher_id,
                save_pitcher_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (schedule_id,) + vals)
        db.commit()
        return cursor.lastrowid


def get_game_detail(game_id: int) -> dict[str, Any] | None:
    """Get complete game data for the read-only detail page."""
    db = get_db()

    game = db.execute("""
        SELECT g.*, s.game_num, s.phase, s.home_team_id, s.away_team_id,
            ht.name as home_name, ht.short_name as home_short,
            ht.color_primary as home_color, ht.logo_file as home_logo,
            at.name as away_name, at.short_name as away_short,
            at.color_primary as away_color, at.logo_file as away_logo,
            wp.name as wp_name, lp.name as lp_name, sp.name as sv_name
        FROM games g
        JOIN schedule s ON g.schedule_id = s.id
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        LEFT JOIN players wp ON g.winning_pitcher_id = wp.id
        LEFT JOIN players lp ON g.losing_pitcher_id = lp.id
        LEFT JOIN players sp ON g.save_pitcher_id = sp.id
        WHERE g.id = ?
    """, (game_id,)).fetchone()

    if not game:
        return None

    home_batting = db.execute("""
        SELECT bs.*, p.name, p.position FROM batting_stats bs
        JOIN players p ON bs.player_id = p.id
        WHERE bs.game_id = ? AND bs.team_id = ?
        ORDER BY bs.id
    """, (game_id, game['home_team_id'])).fetchall()

    away_batting = db.execute("""
        SELECT bs.*, p.name, p.position FROM batting_stats bs
        JOIN players p ON bs.player_id = p.id
        WHERE bs.game_id = ? AND bs.team_id = ?
        ORDER BY bs.id
    """, (game_id, game['away_team_id'])).fetchall()

    home_pitching = db.execute("""
        SELECT ps.*, p.name FROM pitching_stats ps
        JOIN players p ON ps.player_id = p.id
        WHERE ps.game_id = ? AND ps.team_id = ?
        ORDER BY ps.id
    """, (game_id, game['home_team_id'])).fetchall()

    away_pitching = db.execute("""
        SELECT ps.*, p.name FROM pitching_stats ps
        JOIN players p ON ps.player_id = p.id
        WHERE ps.game_id = ? AND ps.team_id = ?
        ORDER BY ps.id
    """, (game_id, game['away_team_id'])).fetchall()

    return {
        'game': game,
        'home_batting': home_batting,
        'away_batting': away_batting,
        'home_pitching': home_pitching,
        'away_pitching': away_pitching,
    }
