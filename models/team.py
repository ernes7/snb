"""Team model — owns every query rooted on a single team.

Consolidates aggregates that were previously re-shaped across
`services/standings.py`, `services/power_rankings.py`, and
`blueprints/teams/services.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from db import get_db
from lib.season import Phase
from lib.stats import BattingLine, PitchingLine

from .base import RowModel


@dataclass(frozen=True)
class TeamRecord:
    """Win/loss/runs tally for a team over some scope.

    `pct` is the formatted string (e.g. ".800") for direct template
    rendering — matches the legacy shape emitted by `services/standings.py`.
    Use `pct_float` for numeric comparisons.
    """
    wins: int
    losses: int
    rs: int  # runs scored
    ra: int  # runs allowed

    @property
    def games(self) -> int:
        return self.wins + self.losses

    @property
    def pct_float(self) -> float:
        return self.wins / self.games if self.games else 0.0

    @property
    def pct(self) -> str:
        return f"{self.pct_float:.3f}" if self.games else ".000"

    @property
    def diff(self) -> int:
        return self.rs - self.ra


class Team(RowModel):
    """A team and every aggregate rooted on it."""

    @classmethod
    def get(cls, short: str) -> Optional["Team"]:
        row = get_db().execute(
            "SELECT * FROM teams WHERE short_name = ?", (short.upper(),)
        ).fetchone()
        return cls(row) if row else None

    @classmethod
    def get_by_id(cls, team_id: int) -> Optional["Team"]:
        row = get_db().execute(
            "SELECT * FROM teams WHERE id = ?", (team_id,)
        ).fetchone()
        return cls(row) if row else None

    @classmethod
    def all(cls) -> list["Team"]:
        rows = get_db().execute("SELECT * FROM teams ORDER BY name").fetchall()
        return [cls(r) for r in rows]

    @classmethod
    def records_for_weeks(
        cls, week_start: int, week_end: int, phase: str = Phase.REGULAR,
    ) -> dict[int, TeamRecord]:
        """{team_id: TeamRecord} restricted to weeks [start, end] inclusive."""
        rows = get_db().execute("""
            SELECT t.id AS team_id,
                COALESCE(SUM(CASE WHEN (s.home_team_id=t.id AND g.home_runs>g.away_runs)
                    OR (s.away_team_id=t.id AND g.away_runs>g.home_runs) THEN 1 ELSE 0 END), 0) AS wins,
                COALESCE(SUM(CASE WHEN (s.home_team_id=t.id AND g.home_runs<g.away_runs)
                    OR (s.away_team_id=t.id AND g.away_runs<g.home_runs) THEN 1 ELSE 0 END), 0) AS losses,
                COALESCE(SUM(CASE WHEN s.home_team_id=t.id THEN g.home_runs
                    WHEN s.away_team_id=t.id THEN g.away_runs ELSE 0 END), 0) AS rs,
                COALESCE(SUM(CASE WHEN s.home_team_id=t.id THEN g.away_runs
                    WHEN s.away_team_id=t.id THEN g.home_runs ELSE 0 END), 0) AS ra
            FROM teams t
            LEFT JOIN schedule s ON (s.home_team_id=t.id OR s.away_team_id=t.id)
                AND s.phase = :phase AND s.week_num BETWEEN :start AND :end
            LEFT JOIN games g ON g.schedule_id = s.id
            GROUP BY t.id
        """, {"phase": phase, "start": week_start, "end": week_end}).fetchall()
        return {
            r["team_id"]: TeamRecord(r["wins"], r["losses"], r["rs"], r["ra"])
            for r in rows
        }

    @classmethod
    def team_stats_all(
        cls, through_week: int | None = None, phase: str = Phase.REGULAR,
    ) -> tuple[dict[int, BattingLine], dict[int, PitchingLine]]:
        """Batch team batting + pitching totals.

        Two queries, grouped by team_id. If `through_week` is None, aggregates
        over all played stats (any phase); otherwise restricts by phase+week.
        Returns ({team_id: BattingLine or None}, {team_id: PitchingLine or None}).
        Teams with zero AB / zero IP_outs are absent from their map.
        """
        db = get_db()
        if through_week is None:
            bat_rows = db.execute("""
                SELECT team_id,
                    SUM(AB) AS AB, SUM(R) AS R, SUM(H) AS H,
                    SUM(doubles) AS doubles, SUM(triples) AS triples,
                    SUM(HR) AS HR, SUM(RBI) AS RBI, SUM(BB) AS BB,
                    SUM(SO) AS SO, SUM(SB) AS SB
                FROM batting_stats GROUP BY team_id HAVING SUM(AB) > 0
            """).fetchall()
            pit_rows = db.execute("""
                SELECT team_id,
                    SUM(IP_outs) AS IP_outs, SUM(H) AS H, SUM(R) AS R,
                    SUM(ER) AS ER, SUM(BB) AS BB, SUM(SO) AS SO,
                    SUM(HR_allowed) AS HR_allowed,
                    SUM(W) AS W, SUM(L) AS L, SUM(SV) AS SV
                FROM pitching_stats GROUP BY team_id HAVING SUM(IP_outs) > 0
            """).fetchall()
        else:
            params = (phase, through_week)
            bat_rows = db.execute("""
                SELECT bs.team_id,
                    SUM(bs.AB) AS AB, SUM(bs.R) AS R, SUM(bs.H) AS H,
                    SUM(bs.doubles) AS doubles, SUM(bs.triples) AS triples,
                    SUM(bs.HR) AS HR, SUM(bs.RBI) AS RBI, SUM(bs.BB) AS BB,
                    SUM(bs.SO) AS SO, SUM(bs.SB) AS SB
                FROM batting_stats bs
                JOIN games g ON bs.game_id = g.id
                JOIN schedule s ON g.schedule_id = s.id
                WHERE s.phase = ? AND s.week_num <= ?
                GROUP BY bs.team_id HAVING SUM(bs.AB) > 0
            """, params).fetchall()
            pit_rows = db.execute("""
                SELECT ps.team_id,
                    SUM(ps.IP_outs) AS IP_outs, SUM(ps.H) AS H, SUM(ps.R) AS R,
                    SUM(ps.ER) AS ER, SUM(ps.BB) AS BB, SUM(ps.SO) AS SO,
                    SUM(ps.HR_allowed) AS HR_allowed,
                    SUM(ps.W) AS W, SUM(ps.L) AS L, SUM(ps.SV) AS SV
                FROM pitching_stats ps
                JOIN games g ON ps.game_id = g.id
                JOIN schedule s ON g.schedule_id = s.id
                WHERE s.phase = ? AND s.week_num <= ?
                GROUP BY ps.team_id HAVING SUM(ps.IP_outs) > 0
            """, params).fetchall()
        bat = {r["team_id"]: BattingLine.from_row(r) for r in bat_rows}
        pit = {r["team_id"]: PitchingLine.from_row(r) for r in pit_rows}
        return bat, pit

    @classmethod
    def records_all(
        cls, through_week: int | None = None, phase: str = Phase.REGULAR,
    ) -> dict[int, TeamRecord]:
        """Batch: one query returns {team_id: TeamRecord} for every team.

        Replaces per-team loops that ran 8 separate queries. Teams with no
        played games appear with a zeroed record.
        """
        params: dict = {"phase": phase}
        week_clause = ""
        if through_week is not None:
            week_clause = "AND s.week_num <= :week"
            params["week"] = through_week
        rows = get_db().execute(f"""
            SELECT t.id AS team_id,
                COALESCE(SUM(CASE WHEN (s.home_team_id=t.id AND g.home_runs>g.away_runs)
                    OR (s.away_team_id=t.id AND g.away_runs>g.home_runs) THEN 1 ELSE 0 END), 0) AS wins,
                COALESCE(SUM(CASE WHEN (s.home_team_id=t.id AND g.home_runs<g.away_runs)
                    OR (s.away_team_id=t.id AND g.away_runs<g.home_runs) THEN 1 ELSE 0 END), 0) AS losses,
                COALESCE(SUM(CASE WHEN s.home_team_id=t.id THEN g.home_runs
                    WHEN s.away_team_id=t.id THEN g.away_runs ELSE 0 END), 0) AS rs,
                COALESCE(SUM(CASE WHEN s.home_team_id=t.id THEN g.away_runs
                    WHEN s.away_team_id=t.id THEN g.home_runs ELSE 0 END), 0) AS ra
            FROM teams t
            LEFT JOIN schedule s ON (s.home_team_id=t.id OR s.away_team_id=t.id)
                AND s.phase = :phase {week_clause}
            LEFT JOIN games g ON g.schedule_id = s.id
            GROUP BY t.id
        """, params).fetchall()
        return {
            r["team_id"]: TeamRecord(r["wins"], r["losses"], r["rs"], r["ra"])
            for r in rows
        }

    # ---- records / standings ----------------------------------------------

    def record(
        self, through_week: int | None = None, phase: str = Phase.REGULAR,
    ) -> TeamRecord:
        """W/L/RS/RA for this team.

        `through_week` restricts to schedule.week_num <= N (inclusive).
        `phase` restricts to a specific phase bucket.
        """
        params: dict = {"tid": self.id, "phase": phase}
        week_clause = ""
        if through_week is not None:
            week_clause = "AND s.week_num <= :week"
            params["week"] = through_week
        row = get_db().execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN (s.home_team_id=:tid AND g.home_runs>g.away_runs)
                    OR (s.away_team_id=:tid AND g.away_runs>g.home_runs) THEN 1 ELSE 0 END), 0) AS wins,
                COALESCE(SUM(CASE WHEN (s.home_team_id=:tid AND g.home_runs<g.away_runs)
                    OR (s.away_team_id=:tid AND g.away_runs<g.home_runs) THEN 1 ELSE 0 END), 0) AS losses,
                COALESCE(SUM(CASE WHEN s.home_team_id=:tid THEN g.home_runs
                    WHEN s.away_team_id=:tid THEN g.away_runs ELSE 0 END), 0) AS rs,
                COALESCE(SUM(CASE WHEN s.home_team_id=:tid THEN g.away_runs
                    WHEN s.away_team_id=:tid THEN g.home_runs ELSE 0 END), 0) AS ra
            FROM games g JOIN schedule s ON g.schedule_id = s.id
            WHERE s.phase = :phase
              AND (s.home_team_id = :tid OR s.away_team_id = :tid)
              {week_clause}
        """, params).fetchone()
        return TeamRecord(row["wins"], row["losses"], row["rs"], row["ra"])

    def h2h_vs(self, other: "Team" | int, phase: str = Phase.REGULAR) -> TeamRecord:
        """Head-to-head record of `self` against `other`."""
        other_id = other.id if isinstance(other, Team) else other
        row = get_db().execute("""
            SELECT
                COALESCE(SUM(CASE WHEN (s.home_team_id=:a AND g.home_runs>g.away_runs)
                    OR (s.away_team_id=:a AND g.away_runs>g.home_runs) THEN 1 ELSE 0 END), 0) AS wins,
                COALESCE(SUM(CASE WHEN (s.home_team_id=:a AND g.home_runs<g.away_runs)
                    OR (s.away_team_id=:a AND g.away_runs<g.home_runs) THEN 1 ELSE 0 END), 0) AS losses,
                COALESCE(SUM(CASE WHEN s.home_team_id=:a THEN g.home_runs
                    WHEN s.away_team_id=:a THEN g.away_runs ELSE 0 END), 0) AS rs,
                COALESCE(SUM(CASE WHEN s.home_team_id=:a THEN g.away_runs
                    WHEN s.away_team_id=:a THEN g.home_runs ELSE 0 END), 0) AS ra
            FROM games g JOIN schedule s ON g.schedule_id = s.id
            WHERE s.phase = :phase
              AND ((s.home_team_id=:a AND s.away_team_id=:b)
                OR (s.home_team_id=:b AND s.away_team_id=:a))
        """, {"a": self.id, "b": other_id, "phase": phase}).fetchone()
        return TeamRecord(row["wins"], row["losses"], row["rs"], row["ra"])

    # ---- roster ----------------------------------------------------------

    def roster_by_role(self) -> dict[str, list]:
        """Roster split by role. Values are Player objects."""
        from .player import Player
        rows = get_db().execute("""
            SELECT * FROM players WHERE team_id = ?
            ORDER BY role, lineup_order, name
        """, (self.id,)).fetchall()
        out: dict[str, list] = {
            "lineup": [], "bench": [], "rotation": [], "bullpen": [],
        }
        for r in rows:
            out.setdefault(r["role"], []).append(Player(r))
        return out

    # ---- aggregates ------------------------------------------------------

    def batting_totals(
        self, through_week: int | None = None, phase: str = Phase.REGULAR,
    ) -> BattingLine | None:
        """Aggregate batting line. If `through_week` is given, joins schedule
        and restricts to `phase` + `week_num <= N`."""
        if through_week is None:
            row = get_db().execute("""
                SELECT SUM(AB) AS AB, SUM(R) AS R, SUM(H) AS H,
                    SUM(doubles) AS doubles, SUM(triples) AS triples,
                    SUM(HR) AS HR, SUM(RBI) AS RBI, SUM(BB) AS BB,
                    SUM(SO) AS SO, SUM(SB) AS SB
                FROM batting_stats WHERE team_id = ?
            """, (self.id,)).fetchone()
        else:
            row = get_db().execute("""
                SELECT SUM(bs.AB) AS AB, SUM(bs.R) AS R, SUM(bs.H) AS H,
                    SUM(bs.doubles) AS doubles, SUM(bs.triples) AS triples,
                    SUM(bs.HR) AS HR, SUM(bs.RBI) AS RBI, SUM(bs.BB) AS BB,
                    SUM(bs.SO) AS SO, SUM(bs.SB) AS SB
                FROM batting_stats bs
                JOIN games g ON bs.game_id = g.id
                JOIN schedule s ON g.schedule_id = s.id
                WHERE bs.team_id = ? AND s.phase = ? AND s.week_num <= ?
            """, (self.id, phase, through_week)).fetchone()
        if not row or not row["AB"]:
            return None
        return BattingLine.from_row(row)

    def pitching_totals(
        self, through_week: int | None = None, phase: str = Phase.REGULAR,
    ) -> PitchingLine | None:
        if through_week is None:
            row = get_db().execute("""
                SELECT SUM(IP_outs) AS IP_outs, SUM(H) AS H, SUM(R) AS R,
                    SUM(ER) AS ER, SUM(BB) AS BB, SUM(SO) AS SO,
                    SUM(HR_allowed) AS HR_allowed,
                    SUM(W) AS W, SUM(L) AS L, SUM(SV) AS SV
                FROM pitching_stats WHERE team_id = ?
            """, (self.id,)).fetchone()
        else:
            row = get_db().execute("""
                SELECT SUM(ps.IP_outs) AS IP_outs, SUM(ps.H) AS H, SUM(ps.R) AS R,
                    SUM(ps.ER) AS ER, SUM(ps.BB) AS BB, SUM(ps.SO) AS SO,
                    SUM(ps.HR_allowed) AS HR_allowed,
                    SUM(ps.W) AS W, SUM(ps.L) AS L, SUM(ps.SV) AS SV
                FROM pitching_stats ps
                JOIN games g ON ps.game_id = g.id
                JOIN schedule s ON g.schedule_id = s.id
                WHERE ps.team_id = ? AND s.phase = ? AND s.week_num <= ?
            """, (self.id, phase, through_week)).fetchone()
        if not row or not row["IP_outs"]:
            return None
        return PitchingLine.from_row(row)

    def errors_committed(self) -> int:
        row = get_db().execute("""
            SELECT COALESCE(SUM(
                CASE WHEN s.home_team_id = :tid THEN g.home_errors
                     WHEN s.away_team_id = :tid THEN g.away_errors
                     ELSE 0 END
            ), 0) AS errors
            FROM games g JOIN schedule s ON g.schedule_id = s.id
            WHERE s.home_team_id = :tid OR s.away_team_id = :tid
        """, {"tid": self.id}).fetchone()
        return row["errors"] if row else 0

    def bat_leaders(self, limit: int | None = None) -> list[dict]:
        """Batters on this team (by AVG, min 1 AB)."""
        sql = """
            SELECT p.id, p.name, p.position,
                COUNT(*) AS G,
                SUM(bs.AB) AS AB, SUM(bs.R) AS R, SUM(bs.H) AS H,
                SUM(bs.doubles) AS doubles, SUM(bs.triples) AS triples,
                SUM(bs.HR) AS HR, SUM(bs.RBI) AS RBI,
                SUM(bs.BB) AS BB, SUM(bs.SO) AS SO, SUM(bs.SB) AS SB,
                CASE WHEN SUM(bs.AB)>0
                     THEN ROUND(CAST(SUM(bs.H) AS FLOAT)/SUM(bs.AB), 3)
                     ELSE 0 END AS AVG,
                CASE WHEN SUM(bs.AB)+SUM(bs.BB)>0
                     THEN ROUND(
                         CAST(SUM(bs.H)+SUM(bs.BB) AS FLOAT)/(SUM(bs.AB)+SUM(bs.BB))
                         + CAST(SUM(bs.H)+SUM(bs.doubles)+2*SUM(bs.triples)+3*SUM(bs.HR) AS FLOAT)/SUM(bs.AB),
                     3) ELSE 0 END AS OPS
            FROM batting_stats bs
            JOIN players p ON bs.player_id = p.id
            WHERE bs.team_id = ?
            GROUP BY p.id HAVING SUM(bs.AB) > 0
            ORDER BY AVG DESC
        """
        params: list = [self.id]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        return [dict(r) for r in get_db().execute(sql, params).fetchall()]

    def pitch_leaders(self, limit: int | None = None) -> list[dict]:
        """Pitchers on this team (by ERA, min 1 IP)."""
        sql = """
            SELECT p.id, p.name,
                SUM(ps.IP_outs) AS IP_outs, SUM(ps.H) AS H,
                SUM(ps.BB) AS BB, SUM(ps.SO) AS SO,
                SUM(ps.W) AS W, SUM(ps.L) AS L, SUM(ps.SV) AS SV,
                CASE WHEN SUM(ps.IP_outs)>0
                     THEN ROUND(CAST(SUM(ps.ER)*27 AS FLOAT)/SUM(ps.IP_outs), 2)
                     ELSE 0 END AS ERA,
                CASE WHEN SUM(ps.IP_outs)>0
                     THEN ROUND(CAST((SUM(ps.H)+SUM(ps.BB))*3 AS FLOAT)/SUM(ps.IP_outs), 2)
                     ELSE 0 END AS WHIP
            FROM pitching_stats ps
            JOIN players p ON ps.player_id = p.id
            WHERE ps.team_id = ?
            GROUP BY p.id HAVING SUM(ps.IP_outs) > 0
            ORDER BY ERA ASC
        """
        params: list = [self.id]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        return [dict(r) for r in get_db().execute(sql, params).fetchall()]
