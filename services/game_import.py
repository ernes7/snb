"""Game import service — insert complete game data from box score readings."""
from __future__ import annotations

import sqlite3
from typing import Any

from db import get_db


def _ip_to_outs(ip_str: str) -> int:
    """Convert innings pitched string to total outs. '4.2' -> 14, '6.0' -> 18."""
    parts = str(ip_str).split(".")
    innings = int(parts[0])
    extra = int(parts[1]) if len(parts) > 1 else 0
    if extra not in (0, 1, 2):
        raise ValueError(
            f"Invalid IP fraction: '{ip_str}' — fractional part must be 0, 1, or 2"
        )
    return innings * 3 + extra


def _resolve_player(db: sqlite3.Connection, name: str, team_short: str) -> int:
    """Find player ID by name and team short_name."""
    row = db.execute("""
        SELECT p.id FROM players p
        JOIN teams t ON p.team_id = t.id
        WHERE p.name = ? AND t.short_name = ?
    """, (name, team_short)).fetchone()
    if not row:
        raise ValueError(f"Player not found: {name} ({team_short})")
    return row[0]


def _resolve_team(db: sqlite3.Connection, short: str) -> int:
    """Find team ID by short_name."""
    row = db.execute("SELECT id FROM teams WHERE short_name = ?", (short,)).fetchone()
    if not row:
        raise ValueError(f"Team not found: {short}")
    return row[0]


def insert_game(
    schedule_id: int,
    home_runs: int, away_runs: int,
    home_hits: int, away_hits: int,
    home_errors: int, away_errors: int,
    wp: tuple[str, str],
    lp: tuple[str, str],
    sv: tuple[str, str] | None,
    batting: list[dict[str, Any]],
    pitching: list[dict[str, Any]],
    home_linescore: str | None = None,
    away_linescore: str | None = None,
) -> int:
    """Insert or update a complete game with all stats.

    Args:
        schedule_id: Which schedule slot this game fills.
        wp/lp/sv: (player_name, team_short) tuples for W/L/Save pitchers.
        batting: List of dicts with keys:
            name, team, AB, R, H, 2B, 3B, HR, RBI, BB, SO, SB
        pitching: List of dicts with keys:
            name, team, IP, H, R, ER, BB, SO, HR, W, L, SV
        home_linescore: Comma-separated runs per inning, e.g. "2,0,3,1,0,0,0,1,0"
        away_linescore: Comma-separated runs per inning.

    Returns:
        The game ID.
    """
    db = get_db()

    try:
        # Resolve pitcher IDs before touching any tables
        wp_id = _resolve_player(db, wp[0], wp[1])
        lp_id = _resolve_player(db, lp[0], lp[1])
        sv_id = _resolve_player(db, sv[0], sv[1]) if sv else None

        # Upsert game record
        existing = db.execute(
            "SELECT id FROM games WHERE schedule_id = ?", (schedule_id,)
        ).fetchone()

        if existing:
            game_id: int = existing[0]
            db.execute("""
                UPDATE games SET date='', home_runs=?, away_runs=?, home_hits=?,
                    away_hits=?, home_errors=?, away_errors=?,
                    winning_pitcher_id=?, losing_pitcher_id=?,
                    save_pitcher_id=?, notes='',
                    home_linescore=?, away_linescore=?
                WHERE id = ?
            """, (home_runs, away_runs, home_hits, away_hits,
                  home_errors, away_errors, wp_id, lp_id, sv_id,
                  home_linescore, away_linescore, game_id))
            # Clear old stats before re-inserting
            db.execute("DELETE FROM batting_stats WHERE game_id = ?", (game_id,))
            db.execute("DELETE FROM pitching_stats WHERE game_id = ?", (game_id,))
        else:
            cursor = db.execute("""
                INSERT INTO games (schedule_id, date, home_runs, away_runs,
                    home_hits, away_hits, home_errors, away_errors,
                    winning_pitcher_id, losing_pitcher_id, save_pitcher_id, notes,
                    home_linescore, away_linescore)
                VALUES (?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?)
            """, (schedule_id, home_runs, away_runs, home_hits, away_hits,
                  home_errors, away_errors, wp_id, lp_id, sv_id,
                  home_linescore, away_linescore))
            game_id = cursor.lastrowid

        # Insert batting stats
        for b in batting:
            pid = _resolve_player(db, b["name"], b["team"])
            tid = _resolve_team(db, b["team"])
            db.execute("""
                INSERT INTO batting_stats
                    (game_id, player_id, team_id, AB, R, H, doubles, triples,
                     HR, RBI, BB, SO, SB)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (game_id, pid, tid, b["AB"], b["R"], b["H"],
                  b.get("2B", 0), b.get("3B", 0), b.get("HR", 0),
                  b.get("RBI", 0), b.get("BB", 0), b.get("SO", 0),
                  b.get("SB", 0)))

        # Insert pitching stats
        for p in pitching:
            pid = _resolve_player(db, p["name"], p["team"])
            tid = _resolve_team(db, p["team"])
            ip_outs = _ip_to_outs(p["IP"])
            db.execute("""
                INSERT INTO pitching_stats
                    (game_id, player_id, team_id, IP_outs, H, R, ER, BB, SO,
                     HR_allowed, W, L, SV, pitches)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (game_id, pid, tid, ip_outs, p["H"], p["R"], p["ER"],
                  p.get("BB", 0), p.get("SO", 0), p.get("HR", 0),
                  p.get("W", 0), p.get("L", 0), p.get("SV", 0),
                  p.get("pitches", 0)))

        db.commit()
    except Exception:
        db.rollback()
        raise

    # Validate after commit
    errors = validate_game(db, game_id, home_runs, away_runs, home_hits, away_hits)
    if errors:
        print("Validation warnings:")
        for e in errors:
            print(f"  {e}")

    return game_id


def validate_game(db: sqlite3.Connection, game_id: int,
                  home_runs: int, away_runs: int,
                  home_hits: int, away_hits: int) -> list[str]:
    """Validate R/H totals match batting stats. Returns list of mismatch messages."""
    sched = db.execute("""
        SELECT ht.short_name as home, at.short_name as away
        FROM games g JOIN schedule s ON g.schedule_id = s.id
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        WHERE g.id = ?
    """, (game_id,)).fetchone()

    errors: list[str] = []
    for label, short, exp_r, exp_h in [
        ("Home", sched[0], home_runs, home_hits),
        ("Away", sched[1], away_runs, away_hits),
    ]:
        row = db.execute("""
            SELECT SUM(R), SUM(H) FROM batting_stats
            WHERE game_id = ? AND team_id = (SELECT id FROM teams WHERE short_name = ?)
        """, (game_id, short)).fetchone()
        r, h = row[0] or 0, row[1] or 0
        if r != exp_r:
            errors.append(f"{label} ({short}): R={r}, expected {exp_r}")
        if h != exp_h:
            errors.append(f"{label} ({short}): H={h}, expected {exp_h}")

    return errors


def delete_game(schedule_id: int) -> None:
    """Delete a game and all cascade-linked stats/tweets by schedule_id."""
    db = get_db()
    db.execute("DELETE FROM games WHERE schedule_id = ?", (schedule_id,))
    db.commit()
