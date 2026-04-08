"""Leaders blueprint services."""
from __future__ import annotations

import sqlite3

from db import get_db


def get_bat_avg_leaders() -> list[sqlite3.Row]:
    """Top 5 batting average leaders (min 5 AB)."""
    return get_db().execute("""
        SELECT p.id, p.name, p.position, t.short_name, t.color_primary, t.logo_file,
            SUM(bs.AB) as AB, SUM(bs.H) as H, SUM(bs.HR) as HR, SUM(bs.RBI) as RBI,
            ROUND(CAST(SUM(bs.H) AS FLOAT)/SUM(bs.AB), 3) as AVG
        FROM batting_stats bs
        JOIN players p ON bs.player_id=p.id JOIN teams t ON p.team_id=t.id
        GROUP BY p.id HAVING SUM(bs.AB) >= 5
        ORDER BY AVG DESC LIMIT 5
    """).fetchall()


def get_bat_hr_leaders() -> list[sqlite3.Row]:
    """Top 5 home run leaders."""
    return get_db().execute("""
        SELECT p.id, p.name, t.short_name, t.color_primary, t.logo_file, SUM(bs.HR) as HR
        FROM batting_stats bs
        JOIN players p ON bs.player_id=p.id JOIN teams t ON p.team_id=t.id
        GROUP BY p.id HAVING SUM(bs.HR) > 0
        ORDER BY HR DESC LIMIT 5
    """).fetchall()


def get_bat_hits_leaders() -> list[sqlite3.Row]:
    """Top 5 hits leaders."""
    return get_db().execute("""
        SELECT p.id, p.name, t.short_name, t.color_primary, t.logo_file, SUM(bs.H) as H
        FROM batting_stats bs
        JOIN players p ON bs.player_id=p.id JOIN teams t ON p.team_id=t.id
        GROUP BY p.id HAVING SUM(bs.H) > 0
        ORDER BY H DESC LIMIT 5
    """).fetchall()


def get_bat_rbi_leaders() -> list[sqlite3.Row]:
    """Top 5 RBI leaders."""
    return get_db().execute("""
        SELECT p.id, p.name, t.short_name, t.color_primary, t.logo_file, SUM(bs.RBI) as RBI
        FROM batting_stats bs
        JOIN players p ON bs.player_id=p.id JOIN teams t ON p.team_id=t.id
        GROUP BY p.id HAVING SUM(bs.RBI) > 0
        ORDER BY RBI DESC LIMIT 5
    """).fetchall()


def get_pitch_wins_leaders() -> list[sqlite3.Row]:
    """Top 5 wins leaders."""
    return get_db().execute("""
        SELECT p.id, p.name, t.short_name, t.color_primary, t.logo_file,
            SUM(ps.W) as W, SUM(ps.L) as L, SUM(ps.IP_outs) as IP_outs
        FROM pitching_stats ps
        JOIN players p ON ps.player_id=p.id JOIN teams t ON p.team_id=t.id
        GROUP BY p.id HAVING SUM(ps.W) > 0
        ORDER BY W DESC LIMIT 5
    """).fetchall()


def get_pitch_era_leaders() -> list[sqlite3.Row]:
    """Top 5 ERA leaders (min 9 outs / 3 IP)."""
    return get_db().execute("""
        SELECT p.id, p.name, t.short_name, t.color_primary, t.logo_file,
            SUM(ps.IP_outs) as IP_outs, SUM(ps.W) as W, SUM(ps.L) as L, SUM(ps.SO) as SO,
            ROUND(CAST(SUM(ps.ER)*27 AS FLOAT)/SUM(ps.IP_outs), 2) as ERA
        FROM pitching_stats ps
        JOIN players p ON ps.player_id=p.id JOIN teams t ON p.team_id=t.id
        GROUP BY p.id HAVING SUM(ps.IP_outs) >= 9
        ORDER BY ERA ASC LIMIT 5
    """).fetchall()


def get_pitch_so_leaders() -> list[sqlite3.Row]:
    """Top 5 strikeout leaders."""
    return get_db().execute("""
        SELECT p.id, p.name, t.short_name, t.color_primary, t.logo_file,
            SUM(ps.SO) as SO, SUM(ps.IP_outs) as IP_outs
        FROM pitching_stats ps
        JOIN players p ON ps.player_id=p.id JOIN teams t ON p.team_id=t.id
        GROUP BY p.id HAVING SUM(ps.SO) > 0
        ORDER BY SO DESC LIMIT 5
    """).fetchall()
