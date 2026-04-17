"""Week model — one week of the regular season.

Wraps the week_num integer with every aggregate that's bounded to that
week. Previously these lived across services/weekly.py as free functions
that re-derived (start, end) game ranges inline.
"""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from db import get_db
from lib.season import Phase, week_game_range


@dataclass(frozen=True)
class WeekCompletion:
    total: int      # schedule rows for the week
    played: int     # games with both scores entered
    boxscored: int  # games with batting_stats entries

    @property
    def is_complete(self) -> bool:
        return self.total > 0 and self.boxscored == self.total


class Week:
    """A regular-season week. Read-only view over schedule + games."""

    __slots__ = ("week_num",)

    def __init__(self, week_num: int) -> None:
        self.week_num = week_num

    def __repr__(self) -> str:
        return f"<Week {self.week_num}>"

    @classmethod
    def latest_with_games(cls, phase: str = Phase.REGULAR) -> int:
        """Return the highest week_num that has at least one played game.

        Used by `/weekly` as the default when no `week_num` is in the URL.
        Falls back to 1 if nothing has been played yet.
        """
        row = get_db().execute("""
            SELECT MAX(s.week_num) AS w
            FROM schedule s
            JOIN games g ON g.schedule_id = s.id
            WHERE s.phase = ?
        """, (phase,)).fetchone()
        return row["w"] or 1

    @property
    def game_range(self) -> tuple[int, int]:
        """Inclusive (first_game_num, last_game_num) for this week."""
        return week_game_range(self.week_num)

    def completion(self, phase: str = Phase.REGULAR) -> WeekCompletion:
        db = get_db()
        total = db.execute(
            "SELECT COUNT(*) FROM schedule WHERE phase=? AND week_num=?",
            (phase, self.week_num),
        ).fetchone()[0]
        played = db.execute("""
            SELECT COUNT(*) FROM games g
            JOIN schedule s ON g.schedule_id = s.id
            WHERE s.phase=? AND s.week_num=?
              AND g.home_runs IS NOT NULL AND g.away_runs IS NOT NULL
        """, (phase, self.week_num)).fetchone()[0]
        boxscored = db.execute("""
            SELECT COUNT(DISTINCT g.id) FROM games g
            JOIN schedule s ON g.schedule_id = s.id
            JOIN batting_stats bs ON bs.game_id = g.id
            WHERE s.phase=? AND s.week_num=?
        """, (phase, self.week_num)).fetchone()[0]
        return WeekCompletion(total=total, played=played, boxscored=boxscored)

    def top_batters(self, limit: int = 5) -> list[sqlite3.Row]:
        """Top batters by composite score (H + 2*HR + RBI)."""
        start, end = self.game_range
        return get_db().execute("""
            SELECT p.id, p.name, t.short_name,
                SUM(bs.AB) AS AB, SUM(bs.H) AS H, SUM(bs.HR) AS HR,
                SUM(bs.RBI) AS RBI, SUM(bs.doubles) AS doubles,
                SUM(bs.triples) AS triples, SUM(bs.BB) AS BB,
                SUM(bs.SO) AS SO, SUM(bs.SB) AS SB, SUM(bs.R) AS R,
                ROUND(CAST(SUM(bs.H) AS FLOAT) / MAX(SUM(bs.AB), 1), 3) AS AVG,
                (SUM(bs.H) + 2 * SUM(bs.HR) + SUM(bs.RBI)) AS score
            FROM batting_stats bs
            JOIN players p ON bs.player_id = p.id
            JOIN teams t ON p.team_id = t.id
            JOIN games g ON bs.game_id = g.id
            JOIN schedule s ON g.schedule_id = s.id
            WHERE s.phase = 'regular' AND s.game_num BETWEEN ? AND ?
            GROUP BY p.id
            HAVING SUM(bs.AB) > 0
            ORDER BY score DESC
            LIMIT ?
        """, (start, end, limit)).fetchall()

    def top_pitchers(self, limit: int = 5) -> list[sqlite3.Row]:
        """Top pitchers by composite score (IP_outs + 2*SO - 3*ER)."""
        start, end = self.game_range
        return get_db().execute("""
            SELECT p.id, p.name, t.short_name,
                SUM(ps.IP_outs) AS IP_outs, SUM(ps.H) AS H,
                SUM(ps.R) AS R, SUM(ps.ER) AS ER,
                SUM(ps.BB) AS BB, SUM(ps.SO) AS SO,
                SUM(ps.HR_allowed) AS HR_allowed,
                SUM(ps.W) AS W, SUM(ps.L) AS L, SUM(ps.SV) AS SV,
                (SUM(ps.IP_outs) + 2 * SUM(ps.SO) - 3 * SUM(ps.ER)) AS score
            FROM pitching_stats ps
            JOIN players p ON ps.player_id = p.id
            JOIN teams t ON p.team_id = t.id
            JOIN games g ON ps.game_id = g.id
            JOIN schedule s ON g.schedule_id = s.id
            WHERE s.phase = 'regular' AND s.game_num BETWEEN ? AND ?
            GROUP BY p.id
            HAVING SUM(ps.IP_outs) > 0
            ORDER BY score DESC
            LIMIT ?
        """, (start, end, limit)).fetchall()
