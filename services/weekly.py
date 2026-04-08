"""Weekly summary and awards services."""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from db import get_db
from lib.utils import format_ip


def get_week_games(week_num: int) -> list[sqlite3.Row]:
    """Get all game results for a given week (4 games per week)."""
    db = get_db()
    start = (week_num - 1) * 4 + 1
    end = week_num * 4
    return db.execute("""
        SELECT g.*, s.game_num,
            ht.short_name as home_short, ht.name as home_name,
            at.short_name as away_short, at.name as away_name,
            wp.name as wp_name, lp.name as lp_name, sp.name as sv_name
        FROM games g
        JOIN schedule s ON g.schedule_id = s.id
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        LEFT JOIN players wp ON g.winning_pitcher_id = wp.id
        LEFT JOIN players lp ON g.losing_pitcher_id = lp.id
        LEFT JOIN players sp ON g.save_pitcher_id = sp.id
        WHERE s.phase = 'regular' AND s.game_num BETWEEN ? AND ?
        ORDER BY s.game_num
    """, (start, end)).fetchall()


def get_week_top_batters(week_num: int, limit: int = 5) -> list[sqlite3.Row]:
    """Top batters for the week by a composite score (H + 2*HR + RBI)."""
    db = get_db()
    start = (week_num - 1) * 4 + 1
    end = week_num * 4
    return db.execute("""
        SELECT p.id, p.name, t.short_name,
            SUM(bs.AB) as AB, SUM(bs.H) as H, SUM(bs.HR) as HR,
            SUM(bs.RBI) as RBI, SUM(bs.doubles) as doubles,
            SUM(bs.triples) as triples, SUM(bs.BB) as BB, SUM(bs.SO) as SO,
            SUM(bs.SB) as SB, SUM(bs.R) as R,
            ROUND(CAST(SUM(bs.H) AS FLOAT) / MAX(SUM(bs.AB), 1), 3) as AVG,
            (SUM(bs.H) + 2 * SUM(bs.HR) + SUM(bs.RBI)) as score
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


def get_week_top_pitchers(week_num: int, limit: int = 5) -> list[sqlite3.Row]:
    """Top pitchers for the week by composite score (IP_outs + 2*SO - 3*ER)."""
    db = get_db()
    start = (week_num - 1) * 4 + 1
    end = week_num * 4
    return db.execute("""
        SELECT p.id, p.name, t.short_name,
            SUM(ps.IP_outs) as IP_outs, SUM(ps.H) as H,
            SUM(ps.R) as R, SUM(ps.ER) as ER,
            SUM(ps.BB) as BB, SUM(ps.SO) as SO,
            SUM(ps.HR_allowed) as HR_allowed,
            SUM(ps.W) as W, SUM(ps.L) as L, SUM(ps.SV) as SV,
            (SUM(ps.IP_outs) + 2 * SUM(ps.SO) - 3 * SUM(ps.ER)) as score
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


def get_analysts_compact() -> list[sqlite3.Row]:
    """Get analyst info in compact form for weekly prompts."""
    return get_db().execute("""
        SELECT a.id, a.handle, a.estilo, a.frase, a.emoji,
            ft.short_name as fav_team, ht.short_name as hate_team
        FROM analysts a
        LEFT JOIN teams ft ON a.equipo_favorito_id = ft.id
        LEFT JOIN teams ht ON a.equipo_odia_id = ht.id
        ORDER BY a.id
    """).fetchall()


def save_weekly_awards(
    week_num: int,
    potw_player_id: int,
    potw_summary: str,
    power_rankings: list[dict[str, Any]],
) -> None:
    """Save Player of the Week and power rankings for a week."""
    db = get_db()
    db.execute("""
        INSERT INTO weekly_awards (week_num, potw_player_id, potw_summary, power_rankings)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(week_num) DO UPDATE SET
            potw_player_id = excluded.potw_player_id,
            potw_summary = excluded.potw_summary,
            power_rankings = excluded.power_rankings
    """, (week_num, potw_player_id, potw_summary, json.dumps(power_rankings)))
    db.commit()


def save_weekly_tweets(
    week_num: int,
    tweets: list[dict[str, Any]],
) -> None:
    """Save analyst tweets for a week. Clears existing weekly tweets first."""
    db = get_db()
    db.execute(
        "DELETE FROM analyst_tweets WHERE week_num = ?", (week_num,)
    )
    for t in tweets:
        db.execute("""
            INSERT INTO analyst_tweets (analyst_id, game_id, texto, week_num)
            VALUES (?, ?, ?, ?)
        """, (t["analyst_id"], t.get("game_id"), t["texto"], week_num))
    db.commit()


def get_weekly_data(week_num: int) -> dict[str, Any] | None:
    """Get all weekly data for display on the /weekly page."""
    db = get_db()

    games = get_week_games(week_num)
    if not games:
        return None

    award = db.execute(
        "SELECT * FROM weekly_awards WHERE week_num = ?", (week_num,)
    ).fetchone()

    potw_player = None
    rankings = []
    if award:
        if award["potw_player_id"]:
            potw_player = db.execute("""
                SELECT p.*, t.short_name, t.color_primary, t.logo_file
                FROM players p JOIN teams t ON p.team_id = t.id
                WHERE p.id = ?
            """, (award["potw_player_id"],)).fetchone()
        if award["power_rankings"]:
            raw = json.loads(award["power_rankings"])
            for entry in raw:
                team = db.execute("""
                    SELECT name, short_name, color_primary, logo_file
                    FROM teams WHERE id = ?
                """, (entry["team_id"],)).fetchone()
                rankings.append({**entry, "team": team})

    tweets = db.execute("""
        SELECT at.*, a.handle, a.emoji, a.avatar_file
        FROM analyst_tweets at
        JOIN analysts a ON at.analyst_id = a.id
        WHERE at.week_num = ?
        ORDER BY at.id
    """, (week_num,)).fetchall()

    return {
        "week_num": week_num,
        "games": games,
        "potw_player": potw_player,
        "potw_summary": award["potw_summary"] if award else None,
        "rankings": rankings,
        "tweets": tweets,
    }
