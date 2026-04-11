"""Shared per-player stat aggregates — single source of truth for player totals.

Both `/leaders` and `/mvp-race` consume these. Each function fetches raw
SUM() aggregates joined with team info, wraps the row in a `BattingLine`
or `PitchingLine` from `lib/stats.py`, then returns a flat dict containing
both identity columns and every rate stat as a key. Dict form (rather
than a dataclass) lets the existing `leaderboard_table` macro read
values via `p[key]` subscript access.
"""
from __future__ import annotations

from typing import Any

from db import get_db
from lib.stats import BattingLine, PitchingLine


def get_all_batting_lines() -> list[dict[str, Any]]:
    """All players with at least one batting appearance, keyed stats merged in."""
    rows = get_db().execute("""
        SELECT p.id, p.name, p.position, p.team_id,
            t.short_name, t.color_primary, t.logo_file,
            SUM(bs.AB) as AB, SUM(bs.R) as R, SUM(bs.H) as H,
            SUM(bs.doubles) as doubles, SUM(bs.triples) as triples,
            SUM(bs.HR) as HR, SUM(bs.RBI) as RBI,
            SUM(bs.BB) as BB, SUM(bs.SO) as SO, SUM(bs.SB) as SB
        FROM batting_stats bs
        JOIN players p ON bs.player_id=p.id JOIN teams t ON p.team_id=t.id
        GROUP BY p.id
    """).fetchall()
    entries = []
    for r in rows:
        line = BattingLine.from_row(r)
        entries.append({
            "id": r["id"], "name": r["name"], "position": r["position"],
            "team_id": r["team_id"], "short_name": r["short_name"],
            "color_primary": r["color_primary"], "logo_file": r["logo_file"],
            "AB": line.AB, "R": line.R, "H": line.H,
            "doubles": line.doubles, "triples": line.triples, "HR": line.HR,
            "RBI": line.RBI, "BB": line.BB, "SO": line.SO, "SB": line.SB,
            "AVG": line.AVG, "OBP": line.OBP, "SLG": line.SLG, "OPS": line.OPS,
            "TB": line.TB, "ISO": line.ISO,
            "_line": line,
        })
    return entries


def get_weekly_batting_series(stat: str = "OPS") -> dict[int, list[float]]:
    """Per-player weekly rate-stat series for sparklines. Returns {player_id: [weekly values]}.

    Buckets every batting_stats row by week_num, wraps each week's SUM() in a BattingLine,
    and reads the requested rate property. One query — no N+1.
    """
    rows = get_db().execute("""
        SELECT bs.player_id, s.week_num,
            SUM(bs.AB) as AB, SUM(bs.R) as R, SUM(bs.H) as H,
            SUM(bs.doubles) as doubles, SUM(bs.triples) as triples,
            SUM(bs.HR) as HR, SUM(bs.RBI) as RBI,
            SUM(bs.BB) as BB, SUM(bs.SO) as SO, SUM(bs.SB) as SB
        FROM batting_stats bs
        JOIN games g ON bs.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        WHERE s.phase = 'regular' AND s.week_num IS NOT NULL
        GROUP BY bs.player_id, s.week_num
        ORDER BY bs.player_id, s.week_num
    """).fetchall()
    series: dict[int, list[float]] = {}
    for r in rows:
        line = BattingLine.from_row(r)
        val = getattr(line, stat, 0.0)
        series.setdefault(r["player_id"], []).append(float(val))
    return series


def get_weekly_pitching_series(stat: str = "ERA") -> dict[int, list[float]]:
    """Per-player weekly pitching rate-stat series for sparklines."""
    rows = get_db().execute("""
        SELECT ps.player_id, s.week_num,
            SUM(ps.IP_outs) as IP_outs, SUM(ps.H) as H, SUM(ps.R) as R,
            SUM(ps.ER) as ER, SUM(ps.BB) as BB, SUM(ps.SO) as SO,
            SUM(ps.HR_allowed) as HR_allowed,
            SUM(ps.W) as W, SUM(ps.L) as L, SUM(ps.SV) as SV
        FROM pitching_stats ps
        JOIN games g ON ps.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        WHERE s.phase = 'regular' AND s.week_num IS NOT NULL
        GROUP BY ps.player_id, s.week_num
        ORDER BY ps.player_id, s.week_num
    """).fetchall()
    series: dict[int, list[float]] = {}
    for r in rows:
        line = PitchingLine.from_row(r)
        val = getattr(line, stat, 0.0)
        series.setdefault(r["player_id"], []).append(float(val))
    return series


def get_all_pitching_lines() -> list[dict[str, Any]]:
    """All players with at least one pitching appearance, keyed stats merged in."""
    rows = get_db().execute("""
        SELECT p.id, p.name, p.team_id,
            t.short_name, t.color_primary, t.logo_file,
            SUM(ps.IP_outs) as IP_outs, SUM(ps.H) as H, SUM(ps.R) as R,
            SUM(ps.ER) as ER, SUM(ps.BB) as BB, SUM(ps.SO) as SO,
            SUM(ps.HR_allowed) as HR_allowed,
            SUM(ps.W) as W, SUM(ps.L) as L, SUM(ps.SV) as SV
        FROM pitching_stats ps
        JOIN players p ON ps.player_id=p.id JOIN teams t ON p.team_id=t.id
        GROUP BY p.id
    """).fetchall()
    entries = []
    for r in rows:
        line = PitchingLine.from_row(r)
        entries.append({
            "id": r["id"], "name": r["name"], "team_id": r["team_id"],
            "short_name": r["short_name"], "color_primary": r["color_primary"],
            "logo_file": r["logo_file"],
            "IP_outs": line.IP_outs, "H": line.H, "R": line.R, "ER": line.ER,
            "BB": line.BB, "SO": line.SO, "HR_allowed": line.HR_allowed,
            "W": line.W, "L": line.L, "SV": line.SV,
            "ERA": line.ERA, "WHIP": line.WHIP, "K9": line.K9,
            "_line": line,
        })
    return entries
