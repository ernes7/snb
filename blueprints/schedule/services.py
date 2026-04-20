"""Schedule blueprint services."""
from __future__ import annotations

import sqlite3
from typing import Any

from db import get_db
from lib.stats import PitchingLine
from lib.utils import format_ip


def get_schedule_games() -> list[sqlite3.Row]:
    """Get all regular season games with team and pitcher info."""
    return get_db().execute("""
        SELECT s.*, g.home_runs, g.away_runs, g.home_hits, g.away_hits,
            g.home_errors, g.away_errors, g.date, g.id as game_id,
            g.winning_pitcher_id as wp_id, g.losing_pitcher_id as lp_id,
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

    # Get ALL appearances (not just latest) so we can accumulate pending rest
    # when an owner pitches a still-resting pitcher out of necessity.
    all_appearances = db.execute("""
        SELECT ps.player_id, ps.team_id, ps.pitches, s.game_num,
            p.name
        FROM pitching_stats ps
        JOIN games g ON ps.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        JOIN players p ON ps.player_id = p.id
        WHERE ps.pitches >= 10 AND s.phase = 'regular'
        ORDER BY ps.player_id, s.game_num
    """).fetchall()

    # Group appearances by pitcher (chronological order from the query).
    pitcher_apps: dict[int, list[dict[str, Any]]] = {}
    for row in all_appearances:
        pitcher_apps.setdefault(row['player_id'], []).append(dict(row))

    # Walk each pitcher's history to compute pending_rest at their last appearance.
    # Rule: if a pitcher pitches while still needing rest, the new rest stacks
    # on top of whatever rest was still owed.
    pitcher_state: dict[int, dict[str, Any]] = {}
    for pid, apps in pitcher_apps.items():
        tid = apps[0]['team_id']
        tg = team_games.get(tid, [])
        pending = 0
        prev_game: int | None = None
        for a in apps:
            gn = a['game_num']
            if prev_game is not None:
                # Count team games elapsed between appearances. The new appearance
                # itself "consumes" a rest slot — the pitcher was supposed to be
                # resting that game but pitched instead, so it counts toward
                # satisfying the previous rest requirement.
                games_between = sum(1 for g in tg if prev_game < g <= gn)
                pending = max(0, pending - games_between)
            pending += _pitches_to_rest(a['pitches'])
            prev_game = gn
        pitcher_state[pid] = {
            'name': apps[-1]['name'],
            'team_id': tid,
            'pitches': apps[-1]['pitches'],
            'game_num': prev_game,
            'rest_needed': pending,
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

            for pid, info in pitcher_state.items():
                if info['team_id'] != tid:
                    continue
                appeared_gnum = info['game_num']
                # Count team games between appearance and this game (exclusive both ends)
                games_rested = sum(1 for gn in tg if appeared_gnum < gn < gnum)
                if games_rested < info['rest_needed']:
                    unavailable.append({
                        'player_id': pid,
                        'name': info['name'],
                        'pitches': info['pitches'],
                        'rest_games': info['rest_needed'],
                        'games_rested': games_rested,
                    })

            if unavailable:
                result[key] = unavailable

    return result


def get_probable_starters() -> dict[str, dict[str, Any]]:
    """Get probable starting pitcher + season stats for each upcoming game + team.

    Returns dict keyed by '{schedule_id}_{team_id}' → {name, W, L, IP, ERA}.
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

    result: dict[str, dict[str, Any]] = {}
    for game in unplayed:
        for tid in (game["home_team_id"], game["away_team_id"]):
            _, name, pid = _get_best_available_pitcher(
                db, tid, game["week_num"], unavailable,
            )
            if not name or not pid:
                continue
            row = db.execute("""
                SELECT SUM(IP_outs) AS IP_outs, SUM(H) AS H, SUM(R) AS R,
                    SUM(ER) AS ER, SUM(BB) AS BB, SUM(SO) AS SO,
                    SUM(HR_allowed) AS HR_allowed,
                    SUM(W) AS W, SUM(L) AS L, SUM(SV) AS SV
                FROM pitching_stats WHERE player_id = ?
            """, (pid,)).fetchone()
            line = PitchingLine.from_row(row)
            result[f"{game['schedule_id']}_{tid}"] = {
                "player_id": pid,
                "name": name,
                "W": line.W,
                "L": line.L,
                "IP": format_ip(line.IP_outs),
                "ERA": line.ERA,
            }
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


def get_moneylines_for_schedule() -> dict[int, list[dict[str, Any]]]:
    """Get player moneylines keyed by schedule_id for display.

    Returns {schedule_id: [{prop_text, prop_type, player_name, team_short,
    team_color, slot}]} sorted by slot.
    """
    db = get_db()
    rows = db.execute("""
        SELECT m.schedule_id, m.prop_text, m.prop_type, m.slot,
            p.name AS player_name, t.short_name AS team_short,
            t.color_primary AS team_color
        FROM game_moneylines m
        JOIN players p ON m.player_id = p.id
        JOIN teams t ON m.team_id = t.id
        ORDER BY m.schedule_id, m.slot
    """).fetchall()
    result: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        result.setdefault(r["schedule_id"], []).append(dict(r))
    return result


def get_team_pitchers_with_stats() -> dict[int, list[dict[str, Any]]]:
    """All rotation + bullpen pitchers per team with season stats.

    Returns {team_id: [{player_id, name, role, IP, ERA, WHIP, W, L, SV}]}
    sorted rotation-first then by ERA within role.
    """
    db = get_db()
    rows = db.execute("""
        SELECT p.id AS player_id, p.name, p.team_id, p.role,
            COALESCE(SUM(ps.IP_outs), 0) AS IP_outs,
            COALESCE(SUM(ps.H), 0) AS H,
            COALESCE(SUM(ps.R), 0) AS R,
            COALESCE(SUM(ps.ER), 0) AS ER,
            COALESCE(SUM(ps.BB), 0) AS BB,
            COALESCE(SUM(ps.SO), 0) AS SO,
            COALESCE(SUM(ps.HR_allowed), 0) AS HR_allowed,
            COALESCE(SUM(ps.W), 0) AS W,
            COALESCE(SUM(ps.L), 0) AS L,
            COALESCE(SUM(ps.SV), 0) AS SV
        FROM players p
        LEFT JOIN pitching_stats ps ON ps.player_id = p.id
        WHERE p.role IN ('rotation', 'bullpen')
        GROUP BY p.id
        ORDER BY p.team_id,
            CASE p.role WHEN 'rotation' THEN 0 ELSE 1 END,
            p.lineup_order
    """).fetchall()
    result: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        line = PitchingLine.from_row(r)
        result.setdefault(r["team_id"], []).append({
            "player_id": r["player_id"],
            "name": r["name"],
            "role": r["role"],
            "IP": format_ip(line.IP_outs),
            "ERA": line.ERA,
            "WHIP": line.WHIP,
            "W": line.W,
            "L": line.L,
            "SV": line.SV,
        })
    return result
