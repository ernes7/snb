"""Teams blueprint services."""
from __future__ import annotations

import sqlite3

from db import get_db
from lib.stats import BattingLine, PitchingLine


def get_team(short_name: str) -> sqlite3.Row | None:
    """Get a team by short name."""
    return get_db().execute(
        "SELECT * FROM teams WHERE short_name=?", (short_name,)
    ).fetchone()


def get_roster(team_id: int) -> tuple[list[sqlite3.Row], list[sqlite3.Row],
                                       list[sqlite3.Row], list[sqlite3.Row]]:
    """Get team roster split by role: lineup, bench, rotation, bullpen."""
    db = get_db()
    lineup = db.execute(
        "SELECT * FROM players WHERE team_id=? AND role='lineup' ORDER BY lineup_order",
        (team_id,)).fetchall()
    bench = db.execute(
        "SELECT * FROM players WHERE team_id=? AND role='bench'",
        (team_id,)).fetchall()
    rotation = db.execute(
        "SELECT * FROM players WHERE team_id=? AND role='rotation' ORDER BY lineup_order",
        (team_id,)).fetchall()
    bullpen = db.execute(
        "SELECT * FROM players WHERE team_id=? AND role='bullpen'",
        (team_id,)).fetchall()
    return lineup, bench, rotation, bullpen


def get_team_bat_leaders(team_id: int) -> list[sqlite3.Row]:
    """Get top 5 batting leaders for a team."""
    return get_db().execute("""
        SELECT p.id, p.name, p.position,
            SUM(bs.AB) as AB, SUM(bs.H) as H, SUM(bs.HR) as HR, SUM(bs.RBI) as RBI,
            CASE WHEN SUM(bs.AB)>0 THEN ROUND(CAST(SUM(bs.H) AS FLOAT)/SUM(bs.AB), 3) ELSE 0 END as AVG
        FROM batting_stats bs
        JOIN players p ON bs.player_id = p.id
        WHERE bs.team_id = ?
        GROUP BY p.id HAVING SUM(bs.AB) > 0
        ORDER BY AVG DESC LIMIT 5
    """, (team_id,)).fetchall()


def get_team_pitch_leaders(team_id: int) -> list[sqlite3.Row]:
    """Get top 5 pitching leaders for a team."""
    return get_db().execute("""
        SELECT p.id, p.name,
            SUM(ps.IP_outs) as IP_outs, SUM(ps.SO) as SO, SUM(ps.W) as W, SUM(ps.L) as L,
            CASE WHEN SUM(ps.IP_outs)>0 THEN ROUND(CAST(SUM(ps.ER)*27 AS FLOAT)/SUM(ps.IP_outs), 2) ELSE 0 END as ERA
        FROM pitching_stats ps
        JOIN players p ON ps.player_id = p.id
        WHERE ps.team_id = ?
        GROUP BY p.id HAVING SUM(ps.IP_outs) > 0
        ORDER BY ERA ASC LIMIT 5
    """, (team_id,)).fetchall()


def get_team_batting_totals(team_id: int) -> BattingLine | None:
    """Get aggregate batting line for a team, or None if no plate appearances."""
    row = get_db().execute("""
        SELECT SUM(AB) as AB, SUM(R) as R, SUM(H) as H,
            SUM(doubles) as doubles, SUM(triples) as triples,
            SUM(HR) as HR, SUM(RBI) as RBI, SUM(BB) as BB,
            SUM(SO) as SO, SUM(SB) as SB
        FROM batting_stats WHERE team_id = ?
    """, (team_id,)).fetchone()
    if not row or not row['AB']:
        return None
    return BattingLine.from_row(row)


def get_team_pitching_totals(team_id: int) -> PitchingLine | None:
    """Get aggregate pitching line for a team, or None if no innings pitched."""
    row = get_db().execute("""
        SELECT SUM(IP_outs) as IP_outs, SUM(H) as H, SUM(R) as R,
            SUM(ER) as ER, SUM(BB) as BB, SUM(SO) as SO,
            SUM(HR_allowed) as HR_allowed
        FROM pitching_stats WHERE team_id = ?
    """, (team_id,)).fetchone()
    if not row or not row['IP_outs']:
        return None
    return PitchingLine.from_row(row)


def get_team_errors(team_id: int) -> int:
    """Get total errors committed by a team across all games."""
    row = get_db().execute("""
        SELECT COALESCE(SUM(
            CASE WHEN s.home_team_id = :tid THEN g.home_errors
                 WHEN s.away_team_id = :tid THEN g.away_errors
                 ELSE 0 END
        ), 0) as errors
        FROM games g JOIN schedule s ON g.schedule_id = s.id
        WHERE s.home_team_id = :tid OR s.away_team_id = :tid
    """, {"tid": team_id}).fetchone()
    return row['errors'] if row else 0
