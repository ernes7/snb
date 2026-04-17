"""Schedule blueprint services."""
from __future__ import annotations

import sqlite3
from typing import Any

from db import get_db


def get_schedule_games() -> list[sqlite3.Row]:
    """Get all regular season games with team and pitcher info."""
    return get_db().execute("""
        SELECT s.*, g.home_runs, g.away_runs, g.home_hits, g.away_hits,
            g.home_errors, g.away_errors, g.date, g.id as game_id,
            ht.name as home_name, ht.short_name as home_short, ht.owner as home_owner,
            ht.color_primary as home_color, ht.logo_file as home_logo,
            at.name as away_name, at.short_name as away_short, at.owner as away_owner,
            at.color_primary as away_color, at.logo_file as away_logo,
            wp.name as wp_name, lp.name as lp_name
        FROM schedule s
        LEFT JOIN teams ht ON s.home_team_id = ht.id
        LEFT JOIN teams at ON s.away_team_id = at.id
        LEFT JOIN games g ON g.schedule_id = s.id
        LEFT JOIN players wp ON g.winning_pitcher_id = wp.id
        LEFT JOIN players lp ON g.losing_pitcher_id = lp.id
        WHERE s.phase = 'regular'
        ORDER BY s.week_num, s.game_num
    """).fetchall()


# (upper_exclusive_pitches, games_to_rest) — first match wins.
PITCH_REST_LADDER: tuple[tuple[int, int], ...] = (
    (10, 0),
    (20, 1),
    (30, 2),
    (40, 3),
    (50, 4),
)
PITCH_REST_MAX = 5


def _pitches_to_rest(pitches: int) -> int:
    """Convert pitch count to mandatory games to miss."""
    for cap, rest in PITCH_REST_LADDER:
        if pitches < cap:
            return rest
    return PITCH_REST_MAX


def get_unavailable_pitchers() -> dict[str, list[dict[str, Any]]]:
    """Get unavailable pitchers for each upcoming game.

    Returns dict keyed by '{schedule_id}_{team_id}' with lists of
    {'name': str, 'pitches': int, 'rest_games': int, 'games_rested': int}.
    """
    db = get_db()

    # Get all team game numbers in order (for counting team games between appearances)
    team_games: dict[int, list[int]] = {}
    for row in db.execute("""
        SELECT s.game_num, s.home_team_id, s.away_team_id
        FROM schedule s WHERE s.phase = 'regular'
        ORDER BY s.game_num
    """).fetchall():
        for tid in (row['home_team_id'], row['away_team_id']):
            team_games.setdefault(tid, []).append(row['game_num'])

    # Find the latest pitch count appearance for each pitcher
    # (only appearances with pitches >= 10 matter for rest)
    latest_appearances = db.execute("""
        SELECT ps.player_id, ps.team_id, ps.pitches, s.game_num,
            p.name
        FROM pitching_stats ps
        JOIN games g ON ps.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        JOIN players p ON ps.player_id = p.id
        WHERE ps.pitches >= 10 AND s.phase = 'regular'
        ORDER BY ps.player_id, s.game_num
    """).fetchall()

    # Group by player, keep only the latest appearance
    pitcher_last: dict[int, dict[str, Any]] = {}
    for row in latest_appearances:
        pid = row['player_id']
        pitcher_last[pid] = {
            'name': row['name'],
            'team_id': row['team_id'],
            'pitches': row['pitches'],
            'game_num': row['game_num'],
            'rest_needed': _pitches_to_rest(row['pitches']),
        }

    # Find unplayed games
    unplayed = db.execute("""
        SELECT s.id as schedule_id, s.game_num, s.home_team_id, s.away_team_id
        FROM schedule s
        LEFT JOIN games g ON g.schedule_id = s.id
        WHERE s.phase = 'regular' AND g.id IS NULL
        ORDER BY s.game_num
    """).fetchall()

    result: dict[str, list[dict[str, Any]]] = {}

    for game in unplayed:
        gnum = game['game_num']
        for tid in (game['home_team_id'], game['away_team_id']):
            key = f"{game['schedule_id']}_{tid}"
            unavailable = []
            tg = team_games.get(tid, [])

            for pid, info in pitcher_last.items():
                if info['team_id'] != tid:
                    continue
                appeared_gnum = info['game_num']
                # Count team games between appearance and this game (exclusive both ends)
                games_rested = sum(1 for gn in tg if appeared_gnum < gn < gnum)
                if games_rested < info['rest_needed']:
                    unavailable.append({
                        'name': info['name'],
                        'pitches': info['pitches'],
                        'rest_games': info['rest_needed'],
                        'games_rested': games_rested,
                    })

            if unavailable:
                result[key] = unavailable

    return result


def get_probable_starters() -> dict[str, str]:
    """Get probable starting pitcher for each upcoming game + team.

    Returns dict keyed by '{schedule_id}_{team_id}' → pitcher name.
    """
    from services.weekly import _get_best_available_pitcher
    db = get_db()
    unavailable = get_unavailable_pitchers()

    unplayed = db.execute("""
        SELECT s.id as schedule_id, s.week_num, s.home_team_id, s.away_team_id
        FROM schedule s
        LEFT JOIN games g ON g.schedule_id = s.id
        WHERE s.phase = 'regular' AND g.id IS NULL
        ORDER BY s.game_num
    """).fetchall()

    result: dict[str, str] = {}
    for game in unplayed:
        for tid in (game["home_team_id"], game["away_team_id"]):
            _, name = _get_best_available_pitcher(
                db, tid, game["week_num"], unavailable,
            )
            if name:
                result[f"{game['schedule_id']}_{tid}"] = name
    return result


def get_game_picks_for_schedule() -> dict[int, list[dict[str, Any]]]:
    """Get analyst game picks keyed by schedule_id.

    Returns {schedule_id: [{analyst_id, handle, avatar_file, emoji, picked_team_id}]}.
    """
    db = get_db()
    rows = db.execute("""
        SELECT p.schedule_id, p.analyst_id, p.picked_team_id,
            a.handle, a.avatar_file, a.emoji
        FROM analyst_game_picks p
        JOIN analysts a ON p.analyst_id = a.id
        ORDER BY p.schedule_id, a.id
    """).fetchall()
    result: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        result.setdefault(r["schedule_id"], []).append(dict(r))
    return result


def get_games_of_week() -> set[int]:
    """Get set of schedule_ids marked as game of the week."""
    db = get_db()
    rows = db.execute(
        "SELECT game_of_week_id FROM weekly_awards WHERE game_of_week_id IS NOT NULL"
    ).fetchall()
    return {r["game_of_week_id"] for r in rows}
