"""Domain models — object-oriented wrappers over DB rows.

Each model (Team, Player, Week, Game) owns the queries about its own
entity. Services consume models; templates read attributes. DB access
stays inside model methods — routes and templates never see raw SQL.

Pattern:
    team = Team.get(short='GRA')
    rec  = team.record()          # returns TeamRecord dataclass
    bats = team.batting_totals()  # returns lib.stats.BattingLine

The goal is to kill re-shaped queries: every aggregate has exactly one
query implementation, named after what it returns.
"""
from __future__ import annotations

from .team import Team, TeamRecord
from .player import Player
from .week import Week
from .game import Game

__all__ = ["Team", "TeamRecord", "Player", "Week", "Game"]
