"""Game model — a single played game, its box score and pitcher decisions."""
from __future__ import annotations

from typing import Optional
import sqlite3

from db import get_db
from lib.season import Phase

from .base import RowModel


class Game(RowModel):
    """A played game. Wraps a row from `games`."""

    @classmethod
    def get(cls, game_id: int) -> Optional["Game"]:
        row = get_db().execute(
            "SELECT * FROM games WHERE id = ?", (game_id,)
        ).fetchone()
        return cls(row) if row else None

    @property
    def is_mercy_rule(self) -> bool:
        """True if the game ended before 9 full innings (linescore shorter)."""
        ls = self.home_linescore or ""
        # Linescore is a pipe-or-comma-separated per-inning string; <9 innings => mercy.
        parts = [p for p in ls.replace("|", ",").split(",") if p.strip()]
        return len(parts) > 0 and len(parts) < 9

    @property
    def total_runs(self) -> int:
        return (self.home_runs or 0) + (self.away_runs or 0)

    def batting_lines(self) -> list[sqlite3.Row]:
        return get_db().execute("""
            SELECT bs.*, p.name, p.position
            FROM batting_stats bs
            JOIN players p ON bs.player_id = p.id
            WHERE bs.game_id = ?
            ORDER BY bs.team_id, bs.id
        """, (self.id,)).fetchall()

    def pitching_lines(self) -> list[sqlite3.Row]:
        return get_db().execute("""
            SELECT ps.*, p.name
            FROM pitching_stats ps
            JOIN players p ON ps.player_id = p.id
            WHERE ps.game_id = ?
            ORDER BY ps.team_id, ps.id
        """, (self.id,)).fetchall()


def _pitcher_cumulative_records() -> dict[tuple[int, int], tuple[int, int, int]]:
    """Build {(player_id, game_id): (cum_W, cum_L, cum_SV)} in one pass.

    Replaces the N correlated SUM() subqueries that appeared per game
    row in `main/services.py` and `services/weekly.py`. One query + a
    Python rollup scales linearly in total pitching lines instead of
    N² in games.
    """
    rows = get_db().execute("""
        SELECT ps.player_id, ps.game_id, ps.W, ps.L, ps.SV
        FROM pitching_stats ps
        ORDER BY ps.player_id, ps.game_id
    """).fetchall()
    out: dict[tuple[int, int], tuple[int, int, int]] = {}
    cur_pid = None
    w = l = sv = 0
    for r in rows:
        if r["player_id"] != cur_pid:
            cur_pid = r["player_id"]
            w = l = sv = 0
        w += r["W"] or 0
        l += r["L"] or 0
        sv += r["SV"] or 0
        out[(r["player_id"], r["game_id"])] = (w, l, sv)
    return out


def _enrich_games_with_pitcher_records(
    games: list[sqlite3.Row],
) -> list[dict]:
    """Attach wp_w/wp_l/lp_w/lp_l/sv_count to each game row as a dict.

    Templates that used these column names (set by the old correlated
    subqueries) keep working unchanged.
    """
    cums = _pitcher_cumulative_records()
    out: list[dict] = []
    for g in games:
        d = dict(g)
        wp_id = g["winning_pitcher_id"]
        lp_id = g["losing_pitcher_id"]
        sp_id = g["save_pitcher_id"]
        d["wp_w"], d["wp_l"] = (cums.get((wp_id, g["id"]), (0, 0, 0))[:2]
                                if wp_id else (None, None))
        d["lp_w"], d["lp_l"] = (cums.get((lp_id, g["id"]), (0, 0, 0))[:2]
                                if lp_id else (None, None))
        d["sv_count"] = (cums.get((sp_id, g["id"]), (0, 0, 0))[2]
                         if sp_id else None)
        out.append(d)
    return out


def recent_games(limit: int = 10) -> list[dict]:
    """Most recent games (any phase) with team info + pitcher decision tallies."""
    rows = get_db().execute("""
        SELECT g.*, s.game_num, s.phase,
            ht.name AS home_name, ht.short_name AS home_short,
            ht.owner AS home_owner, ht.color_primary AS home_color,
            ht.logo_file AS home_logo,
            at.name AS away_name, at.short_name AS away_short,
            at.owner AS away_owner, at.color_primary AS away_color,
            at.logo_file AS away_logo,
            wp.name AS wp_name, lp.name AS lp_name, sp.name AS sp_name
        FROM games g
        JOIN schedule s ON g.schedule_id = s.id
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        LEFT JOIN players wp ON g.winning_pitcher_id = wp.id
        LEFT JOIN players lp ON g.losing_pitcher_id = lp.id
        LEFT JOIN players sp ON g.save_pitcher_id = sp.id
        ORDER BY g.id DESC LIMIT ?
    """, (limit,)).fetchall()
    return _enrich_games_with_pitcher_records(rows)


def week_games(week_num: int, phase: str = Phase.REGULAR) -> list[dict]:
    """All games for a week, with pitcher decision tallies."""
    from lib.season import week_game_range
    start, end = week_game_range(week_num)
    rows = get_db().execute("""
        SELECT g.*, s.game_num,
            ht.short_name AS home_short, ht.name AS home_name,
            ht.color_primary AS home_color, ht.logo_file AS home_logo,
            at.short_name AS away_short, at.name AS away_name,
            at.color_primary AS away_color, at.logo_file AS away_logo,
            wp.name AS wp_name, lp.name AS lp_name, sp.name AS sv_name
        FROM games g
        JOIN schedule s ON g.schedule_id = s.id
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        LEFT JOIN players wp ON g.winning_pitcher_id = wp.id
        LEFT JOIN players lp ON g.losing_pitcher_id = lp.id
        LEFT JOIN players sp ON g.save_pitcher_id = sp.id
        WHERE s.phase = ? AND s.game_num BETWEEN ? AND ?
        ORDER BY s.game_num
    """, (phase, start, end)).fetchall()
    return _enrich_games_with_pitcher_records(rows)
