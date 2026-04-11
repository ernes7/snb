"""Players blueprint services."""
from __future__ import annotations

import sqlite3

from db import get_db
from lib.stats import BattingLine, PitchingLine


def get_player(player_id: int) -> sqlite3.Row | None:
    """Get player with team info."""
    return get_db().execute("""
        SELECT p.*, t.name as team_name, t.short_name as team_short,
            t.color_primary, t.color_secondary, t.owner, t.logo_file
        FROM players p JOIN teams t ON p.team_id = t.id
        WHERE p.id = ?
    """, (player_id,)).fetchone()


def get_player_attrs(player_id: int) -> sqlite3.Row | None:
    """Get player attributes."""
    return get_db().execute(
        "SELECT * FROM player_attributes WHERE player_id=?", (player_id,)
    ).fetchone()


def get_player_draft(player_id: int) -> sqlite3.Row | None:
    """Get player draft info."""
    return get_db().execute("""
        SELECT dp.*, t.name as team_name, t.short_name
        FROM draft_picks dp JOIN teams t ON dp.team_id = t.id
        WHERE dp.player_id = ?
    """, (player_id,)).fetchone()


def get_batting_log(player_id: int) -> list[sqlite3.Row]:
    """Get game-by-game batting stats."""
    return get_db().execute("""
        SELECT bs.*, g.id as game_id, s.game_num, s.phase,
            ht.short_name as home_short, at.short_name as away_short,
            ht.name as home_name, at.name as away_name,
            g.home_runs, g.away_runs
        FROM batting_stats bs
        JOIN games g ON bs.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        WHERE bs.player_id = ?
        ORDER BY s.game_num
    """, (player_id,)).fetchall()


def get_batting_totals(player_id: int) -> BattingLine:
    """Get accumulated batting line (rate stats computed in Python)."""
    row = get_db().execute("""
        SELECT SUM(AB) as AB, SUM(R) as R, SUM(H) as H, SUM(doubles) as doubles,
            SUM(triples) as triples, SUM(HR) as HR, SUM(RBI) as RBI,
            SUM(BB) as BB, SUM(SO) as SO, SUM(SB) as SB
        FROM batting_stats WHERE player_id = ?
    """, (player_id,)).fetchone()
    return BattingLine.from_row(row)


def get_pitching_log(player_id: int) -> list[sqlite3.Row]:
    """Get game-by-game pitching stats."""
    return get_db().execute("""
        SELECT ps.*, g.id as game_id, s.game_num, s.phase,
            ht.short_name as home_short, at.short_name as away_short,
            g.home_runs, g.away_runs
        FROM pitching_stats ps
        JOIN games g ON ps.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        WHERE ps.player_id = ?
        ORDER BY s.game_num
    """, (player_id,)).fetchall()


def get_all_players_with_attrs() -> list[sqlite3.Row]:
    """Get all players with team info and attributes for the database page."""
    return get_db().execute("""
        SELECT p.id, p.name, p.full_name, p.position, p.bats_throws,
            p.role, p.lineup_order, p.bullpen_role, p.is_drafted, p.photo_file,
            t.short_name as team_short, t.name as team_name,
            t.color_primary, t.logo_file, t.owner,
            pa.power_vs_l, pa.contact_vs_l, pa.power_vs_r, pa.contact_vs_r,
            pa.speed, pa.stamina, pa.fastball, pa.slider, pa.curveball,
            pa.sinker, pa.changeup, pa.splitter, pa.screwball,
            pa.cutter, pa.curveball_dirt,
            CASE
                WHEN pa.power_vs_l IS NOT NULL THEN
                    ROUND((pa.power_vs_l + pa.contact_vs_l + pa.power_vs_r + pa.contact_vs_r + pa.speed) / 5.0, 1)
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
            END as overall
        FROM players p
        JOIN teams t ON p.team_id = t.id
        LEFT JOIN player_attributes pa ON pa.player_id = p.id
        ORDER BY overall DESC NULLS LAST, t.id, p.role, p.lineup_order
    """).fetchall()


def get_pitching_totals(player_id: int) -> PitchingLine:
    """Get accumulated pitching line (rate stats computed in Python)."""
    row = get_db().execute("""
        SELECT SUM(IP_outs) as IP_outs, SUM(H) as H, SUM(R) as R, SUM(ER) as ER,
            SUM(BB) as BB, SUM(SO) as SO, SUM(W) as W, SUM(L) as L, SUM(SV) as SV,
            SUM(HR_allowed) as HR_allowed
        FROM pitching_stats WHERE player_id = ?
    """, (player_id,)).fetchone()
    return PitchingLine.from_row(row)
