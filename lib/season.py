"""Season-shape constants and week/game math.

Single source of truth for the tournament's fixed dimensions. Changing
any of these here propagates everywhere — there are no magic numbers
for season shape scattered elsewhere in the codebase.
"""
from __future__ import annotations


GAMES_PER_WEEK = 4
TOTAL_WEEKS = 24
TOTAL_GAMES = GAMES_PER_WEEK * TOTAL_WEEKS  # 96
TEAM_COUNT = 8
NEWSPAPER_EDITIONS = 6


class Phase:
    """Schedule phase values stored in schedule.phase."""
    REGULAR = "regular"
    PLAYOFFS = "playoffs"
    FINALS = "finals"


def week_game_range(week_num: int) -> tuple[int, int]:
    """Return (first_game_num, last_game_num) inclusive for a given week."""
    return ((week_num - 1) * GAMES_PER_WEEK + 1, week_num * GAMES_PER_WEEK)
