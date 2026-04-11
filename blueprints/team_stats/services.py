"""Team stats blueprint services — team-level aggregate leaders.

Pattern: query returns team identity columns + raw SUM() counts, then we
wrap each row in a `BattingLine`/`PitchingLine` so rate stats (AVG/OPS/ERA)
come from the single source of truth in `lib/stats.py`. Sorting happens
in Python after wrapping.
"""
from __future__ import annotations

from dataclasses import dataclass

from db import get_db
from lib.stats import BattingLine, PitchingLine


@dataclass(frozen=True)
class TeamBattingEntry:
    team_id: int
    short_name: str
    name: str
    color_primary: str
    logo_file: str
    line: BattingLine


@dataclass(frozen=True)
class TeamPitchingEntry:
    team_id: int
    short_name: str
    name: str
    color_primary: str
    logo_file: str
    line: PitchingLine


def get_team_batting_leaders() -> list[TeamBattingEntry]:
    """Teams ranked by team OPS descending."""
    rows = get_db().execute("""
        SELECT t.id as team_id, t.short_name, t.name, t.color_primary, t.logo_file,
            SUM(bs.AB) as AB, SUM(bs.R) as R, SUM(bs.H) as H,
            SUM(bs.doubles) as doubles, SUM(bs.triples) as triples,
            SUM(bs.HR) as HR, SUM(bs.RBI) as RBI,
            SUM(bs.BB) as BB, SUM(bs.SO) as SO, SUM(bs.SB) as SB
        FROM batting_stats bs
        JOIN teams t ON bs.team_id = t.id
        GROUP BY t.id HAVING SUM(bs.AB) > 0
    """).fetchall()
    entries = [
        TeamBattingEntry(
            team_id=r["team_id"], short_name=r["short_name"], name=r["name"],
            color_primary=r["color_primary"], logo_file=r["logo_file"],
            line=BattingLine.from_row(r),
        )
        for r in rows
    ]
    return sorted(entries, key=lambda e: e.line.OPS, reverse=True)


def get_team_pitching_leaders() -> list[TeamPitchingEntry]:
    """Teams ranked by team ERA ascending."""
    rows = get_db().execute("""
        SELECT t.id as team_id, t.short_name, t.name, t.color_primary, t.logo_file,
            SUM(ps.IP_outs) as IP_outs, SUM(ps.H) as H, SUM(ps.R) as R,
            SUM(ps.ER) as ER, SUM(ps.BB) as BB, SUM(ps.SO) as SO,
            SUM(ps.HR_allowed) as HR_allowed
        FROM pitching_stats ps
        JOIN teams t ON ps.team_id = t.id
        GROUP BY t.id HAVING SUM(ps.IP_outs) > 0
    """).fetchall()
    entries = [
        TeamPitchingEntry(
            team_id=r["team_id"], short_name=r["short_name"], name=r["name"],
            color_primary=r["color_primary"], logo_file=r["logo_file"],
            line=PitchingLine.from_row(r),
        )
        for r in rows
    ]
    return sorted(entries, key=lambda e: e.line.ERA)
