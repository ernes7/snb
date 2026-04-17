"""Player model — per-player aggregates and relationships."""
from __future__ import annotations

import sqlite3
from typing import Optional

from db import get_db
from lib.stats import BattingLine, PitchingLine

from .base import RowModel


class Player(RowModel):
    """A player and their career aggregates."""

    @classmethod
    def get(cls, player_id: int) -> Optional["Player"]:
        row = get_db().execute(
            "SELECT * FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        return cls(row) if row else None

    @classmethod
    def get_with_team(cls, player_id: int) -> Optional["Player"]:
        """Player with team identity columns merged in (for detail pages)."""
        row = get_db().execute("""
            SELECT p.*, t.name AS team_name, t.short_name AS team_short,
                t.color_primary, t.color_secondary, t.owner, t.logo_file
            FROM players p JOIN teams t ON p.team_id = t.id
            WHERE p.id = ?
        """, (player_id,)).fetchone()
        return cls(row) if row else None

    @classmethod
    def all(cls) -> list["Player"]:
        rows = get_db().execute(
            "SELECT * FROM players ORDER BY team_id, role, lineup_order, name"
        ).fetchall()
        return [cls(r) for r in rows]

    @classmethod
    def all_with_attrs_and_overall(cls) -> list[sqlite3.Row]:
        """Every player + team identity + attributes + computed OVR.

        Powers the `/jugadores` page. Batter OVR = mean of 5 core hitting
        attributes; pitcher OVR = mean of stamina + whichever pitch ratings
        are populated. Sorted by OVR desc, NULLs last.
        """
        return get_db().execute("""
            SELECT p.id, p.name, p.full_name, p.position, p.bats_throws,
                p.role, p.lineup_order, p.bullpen_role, p.is_drafted, p.photo_file,
                t.short_name AS team_short, t.name AS team_name,
                t.color_primary, t.logo_file, t.owner,
                pa.power_vs_l, pa.contact_vs_l, pa.power_vs_r, pa.contact_vs_r,
                pa.speed, pa.stamina, pa.fastball, pa.slider, pa.curveball,
                pa.sinker, pa.changeup, pa.splitter, pa.screwball,
                pa.cutter, pa.curveball_dirt,
                CASE
                    WHEN pa.power_vs_l IS NOT NULL THEN
                        ROUND((pa.power_vs_l + pa.contact_vs_l + pa.power_vs_r
                            + pa.contact_vs_r + pa.speed) / 5.0, 1)
                    WHEN pa.stamina IS NOT NULL THEN
                        ROUND((pa.stamina + COALESCE(pa.fastball,0) + COALESCE(pa.slider,0)
                            + COALESCE(pa.curveball,0) + COALESCE(pa.sinker,0)
                            + COALESCE(pa.changeup,0) + COALESCE(pa.splitter,0)
                            + COALESCE(pa.screwball,0) + COALESCE(pa.cutter,0)
                            + COALESCE(pa.curveball_dirt,0)) * 1.0
                        / (1 + (pa.fastball IS NOT NULL) + (pa.slider IS NOT NULL)
                            + (pa.curveball IS NOT NULL) + (pa.sinker IS NOT NULL)
                            + (pa.changeup IS NOT NULL) + (pa.splitter IS NOT NULL)
                            + (pa.screwball IS NOT NULL) + (pa.cutter IS NOT NULL)
                            + (pa.curveball_dirt IS NOT NULL)), 1)
                    ELSE NULL
                END AS overall
            FROM players p
            JOIN teams t ON p.team_id = t.id
            LEFT JOIN player_attributes pa ON pa.player_id = p.id
            ORDER BY overall DESC NULLS LAST, t.id, p.role, p.lineup_order
        """).fetchall()

    @property
    def is_pitcher(self) -> bool:
        return self.role in ("rotation", "bullpen")

    def batting_line(self) -> BattingLine:
        """Career batting totals — always returns a line (zeroed if none)."""
        row = get_db().execute("""
            SELECT SUM(AB) AS AB, SUM(R) AS R, SUM(H) AS H,
                SUM(doubles) AS doubles, SUM(triples) AS triples,
                SUM(HR) AS HR, SUM(RBI) AS RBI, SUM(BB) AS BB,
                SUM(SO) AS SO, SUM(SB) AS SB
            FROM batting_stats WHERE player_id = ?
        """, (self.id,)).fetchone()
        return BattingLine.from_row(row)

    def pitching_line(self) -> PitchingLine:
        row = get_db().execute("""
            SELECT SUM(IP_outs) AS IP_outs, SUM(H) AS H, SUM(R) AS R,
                SUM(ER) AS ER, SUM(BB) AS BB, SUM(SO) AS SO,
                SUM(HR_allowed) AS HR_allowed,
                SUM(W) AS W, SUM(L) AS L, SUM(SV) AS SV
            FROM pitching_stats WHERE player_id = ?
        """, (self.id,)).fetchone()
        return PitchingLine.from_row(row)

    def attributes(self) -> sqlite3.Row | None:
        return get_db().execute(
            "SELECT * FROM player_attributes WHERE player_id = ?", (self.id,)
        ).fetchone()

    def draft_info(self) -> sqlite3.Row | None:
        return get_db().execute("""
            SELECT dp.*, t.name AS team_name, t.short_name
            FROM draft_picks dp JOIN teams t ON dp.team_id = t.id
            WHERE dp.player_id = ?
        """, (self.id,)).fetchone()

    def batting_log(self) -> list[sqlite3.Row]:
        """Per-game batting lines with opponent team info."""
        return get_db().execute("""
            SELECT bs.*, g.id AS game_id, s.game_num, s.phase,
                ht.short_name AS home_short, at.short_name AS away_short,
                ht.name AS home_name, at.name AS away_name,
                g.home_runs, g.away_runs
            FROM batting_stats bs
            JOIN games g ON bs.game_id = g.id
            JOIN schedule s ON g.schedule_id = s.id
            JOIN teams ht ON s.home_team_id = ht.id
            JOIN teams at ON s.away_team_id = at.id
            WHERE bs.player_id = ?
            ORDER BY s.game_num
        """, (self.id,)).fetchall()

    def pitching_log(self) -> list[sqlite3.Row]:
        """Per-game pitching lines with opponent team info."""
        return get_db().execute("""
            SELECT ps.*, g.id AS game_id, s.game_num, s.phase,
                ht.short_name AS home_short, at.short_name AS away_short,
                g.home_runs, g.away_runs
            FROM pitching_stats ps
            JOIN games g ON ps.game_id = g.id
            JOIN schedule s ON g.schedule_id = s.id
            JOIN teams ht ON s.home_team_id = ht.id
            JOIN teams at ON s.away_team_id = at.id
            WHERE ps.player_id = ?
            ORDER BY s.game_num
        """, (self.id,)).fetchall()

    def batting_sparkline(self) -> list[float]:
        """Per-game OPS series for sparkline rendering (0 on 0-AB games)."""
        return [
            round(BattingLine.from_row(g).OPS, 3) if g["AB"] > 0 else 0.0
            for g in self.batting_log()
        ]

    def pitching_sparkline(self) -> list[float]:
        """Per-game ERA series for sparkline rendering (0 on 0-IP games)."""
        return [
            PitchingLine.from_row(g).ERA if g["IP_outs"] > 0 else 0.0
            for g in self.pitching_log()
        ]
