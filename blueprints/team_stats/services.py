"""Team stats blueprint services — team-level aggregate leaders.

Thin presentation layer over `Team.team_stats_all()`. The model owns the
query; this file wraps each `(team, line)` pair with identity columns
for the template and sorts in Python.
"""
from __future__ import annotations

from dataclasses import dataclass

from lib.stats import BattingLine, PitchingLine
from models import Team


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


def _team_lookup() -> dict[int, Team]:
    return {t.id: t for t in Team.all()}


def get_team_batting_leaders() -> list[TeamBattingEntry]:
    """Teams ranked by team OPS descending."""
    bat_lines, _ = Team.team_stats_all()
    teams = _team_lookup()
    entries = [
        TeamBattingEntry(
            team_id=tid,
            short_name=teams[tid].short_name,
            name=teams[tid].name,
            color_primary=teams[tid].color_primary,
            logo_file=teams[tid].logo_file,
            line=line,
        )
        for tid, line in bat_lines.items() if tid in teams
    ]
    return sorted(entries, key=lambda e: e.line.OPS, reverse=True)


def get_team_pitching_leaders() -> list[TeamPitchingEntry]:
    """Teams ranked by team ERA ascending."""
    _, pit_lines = Team.team_stats_all()
    teams = _team_lookup()
    entries = [
        TeamPitchingEntry(
            team_id=tid,
            short_name=teams[tid].short_name,
            name=teams[tid].name,
            color_primary=teams[tid].color_primary,
            logo_file=teams[tid].logo_file,
            line=line,
        )
        for tid, line in pit_lines.items() if tid in teams
    ]
    return sorted(entries, key=lambda e: e.line.ERA)
