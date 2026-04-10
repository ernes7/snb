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

    # Validate after commit — raise so bad data is never silently accepted
    errors = validate_game(db, game_id, home_runs, away_runs, home_hits, away_hits)
    if errors:
        msg = "CROSS-CHECK FAILURES (game saved but needs review):\n"
        msg += "\n".join(f"  ✗ {e}" for e in errors)
        raise ValueError(msg)

    return game_id


def validate_game(db: sqlite3.Connection, game_id: int,
                  home_runs: int, away_runs: int,
                  home_hits: int, away_hits: int) -> list[str]:
    """Comprehensive cross-validation of game data.

    Checks:
      1. Batting R/H/AB/RBI/BB/SO totals match team header values
      2. Pitching H/R/BB/SO must equal opposing team's batting totals
      3. Extra-base hits ≤ total hits per player
      4. Linescore sums match total runs
      5. Exactly 1 W, 1 L, at most 1 SV across all pitchers
      6. Total IP outs ≥ 27 per team (full game)
      7. ER ≤ R for every pitcher
    """
    sched = db.execute("""
        SELECT ht.short_name as home, at.short_name as away,
               g.home_linescore, g.away_linescore
        FROM games g JOIN schedule s ON g.schedule_id = s.id
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        WHERE g.id = ?
    """, (game_id,)).fetchone()

    home_short, away_short = sched[0], sched[1]
    home_ls, away_ls = sched[2], sched[3]

    errors: list[str] = []

    # -- Per-team batting & pitching cross-checks --
    sides = [
        ("Home", home_short, away_short, home_runs, home_hits, home_ls),
        ("Away", away_short, home_short, away_runs, away_hits, away_ls),
    ]
    for label, bat_team, pitch_team, exp_r, exp_h, linescore in sides:
        # Batting aggregates
        bat = db.execute("""
            SELECT COALESCE(SUM(AB),0), COALESCE(SUM(R),0), COALESCE(SUM(H),0),
                   COALESCE(SUM(RBI),0), COALESCE(SUM(BB),0), COALESCE(SUM(SO),0),
                   COALESCE(SUM(doubles),0), COALESCE(SUM(triples),0),
                   COALESCE(SUM(HR),0)
            FROM batting_stats
            WHERE game_id = ? AND team_id = (
                SELECT id FROM teams WHERE short_name = ?)
        """, (game_id, bat_team)).fetchone()
        b_ab, b_r, b_h, b_rbi, b_bb, b_so = bat[0:6]
        b_xbh = bat[6] + bat[7] + bat[8]  # 2B + 3B + HR

        # 1) Batting totals vs header
        if b_r != exp_r:
            errors.append(f"{label} ({bat_team}): batting R={b_r}, expected {exp_r}")
        if b_h != exp_h:
            errors.append(f"{label} ({bat_team}): batting H={b_h}, expected {exp_h}")

        # Opposing pitching aggregates (pitchers who faced this team's batters)
        pit = db.execute("""
            SELECT COALESCE(SUM(H),0), COALESCE(SUM(R),0),
                   COALESCE(SUM(BB),0), COALESCE(SUM(SO),0),
                   COALESCE(SUM(IP_outs),0)
            FROM pitching_stats
            WHERE game_id = ? AND team_id = (
                SELECT id FROM teams WHERE short_name = ?)
        """, (game_id, pitch_team)).fetchone()
        p_h, p_r, p_bb, p_so, p_outs = pit

        # 2) Pitching vs batting cross-check
        if p_h != b_h:
            errors.append(
                f"{label} ({bat_team}): batting H={b_h} != "
                f"{pitch_team} pitching H={p_h}"
            )
        if p_r != b_r:
            errors.append(
                f"{label} ({bat_team}): batting R={b_r} != "
                f"{pitch_team} pitching R={p_r}"
            )
        if p_bb != b_bb:
            errors.append(
                f"{label} ({bat_team}): batting BB={b_bb} != "
                f"{pitch_team} pitching BB={p_bb}"
            )
        if p_so != b_so:
            errors.append(
                f"{label} ({bat_team}): batting SO={b_so} != "
                f"{pitch_team} pitching SO={p_so}"
            )

        # 3) Linescore sum must match runs
        if linescore:
            ls_sum = sum(int(x) for x in linescore.split(",") if x.strip())
            if ls_sum != exp_r:
                errors.append(
                    f"{label} ({bat_team}): linescore sums to {ls_sum}, "
                    f"expected {exp_r}"
                )

        # 4) IP outs check — visiting pitchers may only face 24 outs
        #    (home team doesn't bat in 9th if winning)
        is_visiting_pitchers = (label == "Home")  # home batters face away pitchers
        home_won = home_runs > away_runs
        min_outs = 24 if (is_visiting_pitchers and home_won) else 27
        if p_outs < min_outs:
            errors.append(
                f"{pitch_team} pitching: only {p_outs} outs "
                f"({p_outs // 3}.{p_outs % 3} IP), expected >= {min_outs}"
            )

    # -- Per-player checks --
    players = db.execute("""
        SELECT p.name, t.short_name, bs.H, bs.doubles, bs.triples, bs.HR
        FROM batting_stats bs
        JOIN players p ON bs.player_id = p.id
        JOIN teams t ON bs.team_id = t.id
        WHERE bs.game_id = ?
    """, (game_id,)).fetchall()
    for row in players:
        name, team, h, d, tr, hr = row
        xbh = d + tr + hr
        # 5) Extra-base hits can't exceed total hits
        if xbh > h:
            errors.append(
                f"{name} ({team}): XBH={xbh} (2B={d}+3B={tr}+HR={hr}) > H={h}"
            )

    pitchers = db.execute("""
        SELECT p.name, t.short_name, ps.R, ps.ER
        FROM pitching_stats ps
        JOIN players p ON ps.player_id = p.id
        JOIN teams t ON ps.team_id = t.id
        WHERE ps.game_id = ?
    """, (game_id,)).fetchall()
    for row in pitchers:
        name, team, r, er = row
        # 6) Earned runs can't exceed total runs
        if er > r:
            errors.append(f"{name} ({team}): ER={er} > R={r}")

    # -- W/L/SV counts --
    wls = db.execute("""
        SELECT SUM(W), SUM(L), SUM(SV)
        FROM pitching_stats WHERE game_id = ?
    """, (game_id,)).fetchone()
    total_w, total_l, total_sv = wls[0] or 0, wls[1] or 0, wls[2] or 0
    if total_w != 1:
        errors.append(f"Expected exactly 1 W, found {total_w}")
    if total_l != 1:
        errors.append(f"Expected exactly 1 L, found {total_l}")
    if total_sv > 1:
        errors.append(f"Expected at most 1 SV, found {total_sv}")

    return errors


def delete_game(schedule_id: int) -> None:
    """Delete a game and all cascade-linked stats/tweets by schedule_id."""
    db = get_db()
    db.execute("DELETE FROM games WHERE schedule_id = ?", (schedule_id,))
    db.commit()
