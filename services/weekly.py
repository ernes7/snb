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
            ht.color_primary as home_color, ht.logo_file as home_logo,
            at.short_name as away_short, at.name as away_name,
            at.color_primary as away_color, at.logo_file as away_logo,
            wp.name as wp_name, lp.name as lp_name, sp.name as sv_name,
            (SELECT SUM(ps.W) FROM pitching_stats ps
             JOIN games g2 ON ps.game_id = g2.id
             WHERE ps.player_id = g.winning_pitcher_id AND g2.id <= g.id) as wp_w,
            (SELECT SUM(ps.L) FROM pitching_stats ps
             JOIN games g2 ON ps.game_id = g2.id
             WHERE ps.player_id = g.winning_pitcher_id AND g2.id <= g.id) as wp_l,
            (SELECT SUM(ps.W) FROM pitching_stats ps
             JOIN games g2 ON ps.game_id = g2.id
             WHERE ps.player_id = g.losing_pitcher_id AND g2.id <= g.id) as lp_w,
            (SELECT SUM(ps.L) FROM pitching_stats ps
             JOIN games g2 ON ps.game_id = g2.id
             WHERE ps.player_id = g.losing_pitcher_id AND g2.id <= g.id) as lp_l,
            (SELECT SUM(ps.SV) FROM pitching_stats ps
             JOIN games g2 ON ps.game_id = g2.id
             WHERE ps.player_id = g.save_pitcher_id AND g2.id <= g.id) as sv_count
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
    game_of_week_id: int | None = None,
) -> None:
    """Save Player of the Week, power rankings, and game of the week."""
    db = get_db()
    db.execute("""
        INSERT INTO weekly_awards (week_num, potw_player_id, potw_summary,
            power_rankings, game_of_week_id)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(week_num) DO UPDATE SET
            potw_player_id = excluded.potw_player_id,
            potw_summary = excluded.potw_summary,
            power_rankings = excluded.power_rankings,
            game_of_week_id = excluded.game_of_week_id
    """, (week_num, potw_player_id, potw_summary,
          json.dumps(power_rankings), game_of_week_id))
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


def _get_rank_map(week_num: int) -> dict[int, int]:
    """Get team_id → rank mapping from a week's power rankings."""
    db = get_db()
    row = db.execute(
        "SELECT power_rankings FROM weekly_awards WHERE week_num = ?",
        (week_num,),
    ).fetchone()
    if not row or not row["power_rankings"]:
        return {}
    return {e["team_id"]: e["rank"] for e in json.loads(row["power_rankings"])}


def _pitcher_ovr(p: sqlite3.Row) -> float:
    """Calculate a pitcher's OVR from their attributes."""
    ratings = [v for v in [
        p["stamina"], p["fastball"], p["slider"], p["curveball"],
        p["sinker"], p["changeup"], p["splitter"], p["screwball"],
        p["cutter"], p["curveball_dirt"],
    ] if v]
    return sum(ratings) / len(ratings) if ratings else 0.0


def _get_best_available_pitcher(
    db: sqlite3.Connection, team_id: int, week_num: int,
    unavailable: dict[str, list[dict[str, Any]]] | None = None,
) -> tuple[float, str | None]:
    """Get the best available starting pitcher's OVR and name for a team.

    Returns (ovr, name) or (0.0, None) if no data.
    """
    if unavailable is None:
        from blueprints.schedule.services import get_unavailable_pitchers
        unavailable = get_unavailable_pitchers()

    # Get schedule_ids for this week to check unavailability
    scheds = db.execute("""
        SELECT id FROM schedule
        WHERE phase = 'regular' AND week_num = ?
        AND (home_team_id = ? OR away_team_id = ?)
    """, (week_num, team_id, team_id)).fetchall()

    unavail_names: set[str] = set()
    for s in scheds:
        key = f"{s['id']}_{team_id}"
        for p in unavailable.get(key, []):
            unavail_names.add(p["name"])

    pitchers = db.execute("""
        SELECT p.name, pa.stamina, pa.fastball, pa.slider, pa.curveball,
            pa.sinker, pa.changeup, pa.splitter, pa.screwball,
            pa.cutter, pa.curveball_dirt
        FROM players p
        LEFT JOIN player_attributes pa ON p.id = pa.player_id
        WHERE p.team_id = ? AND p.role = 'rotation'
        ORDER BY p.lineup_order
    """, (team_id,)).fetchall()

    best_ovr = 0.0
    best_name: str | None = None
    for p in pitchers:
        if p["name"] in unavail_names:
            continue
        ovr = _pitcher_ovr(p)
        if ovr > best_ovr:
            best_ovr = ovr
            best_name = p["name"]
    return best_ovr, best_name


def _get_h2h_record(
    db: sqlite3.Connection, team_a: int, team_b: int,
) -> tuple[int, int]:
    """Get head-to-head wins for team_a vs team_b. Returns (a_wins, b_wins)."""
    rows = db.execute("""
        SELECT
            CASE WHEN (s.home_team_id = ? AND g.home_runs > g.away_runs)
                OR (s.away_team_id = ? AND g.away_runs > g.home_runs)
                THEN 1 ELSE 0 END as a_win,
            CASE WHEN (s.home_team_id = ? AND g.home_runs > g.away_runs)
                OR (s.away_team_id = ? AND g.away_runs > g.home_runs)
                THEN 1 ELSE 0 END as b_win
        FROM games g
        JOIN schedule s ON g.schedule_id = s.id
        WHERE s.phase = 'regular'
        AND ((s.home_team_id = ? AND s.away_team_id = ?)
          OR (s.home_team_id = ? AND s.away_team_id = ?))
    """, (team_a, team_a, team_b, team_b,
          team_a, team_b, team_b, team_a)).fetchall()
    a_wins = sum(r["a_win"] for r in rows)
    b_wins = sum(r["b_win"] for r in rows)
    return a_wins, b_wins


# Analyst personality weights: (fav_bias, rankings, pitching, h2h)
# Higher fav_bias = more likely to pick favorite regardless
# Sum doesn't need to be 1.0 — we compare home_score vs away_score
_ANALYST_WEIGHTS: dict[int, dict[str, float]] = {
    1: {"fav": 0.40, "rank": 0.20, "pitch": 0.25, "h2h": 0.15},  # Panfilo: pitcher + h2h
    2: {"fav": 0.45, "rank": 0.25, "pitch": 0.15, "h2h": 0.15},  # Chequera: heart + rankings
    3: {"fav": 0.35, "rank": 0.25, "pitch": 0.25, "h2h": 0.15},  # Facundo: methodical, pitching
}


def generate_game_picks(week_num: int) -> list[dict[str, Any]]:
    """Generate analyst winner picks for a week's games.

    Weighted scoring per analyst:
      1. Favorite team bias — bonus if fav is playing, penalty if hated
      2. Power rankings — higher ranked team gets edge
      3. Pitcher matchup — best available starter OVR comparison
      4. Head-to-head — prior matchup results
    Each analyst weights these differently per their personality.
    """
    db = get_db()
    rank_map = _get_rank_map(week_num - 1) if week_num > 1 else {}

    games = db.execute("""
        SELECT s.id as schedule_id, s.home_team_id, s.away_team_id
        FROM schedule s
        WHERE s.phase = 'regular' AND s.week_num = ?
        ORDER BY s.game_num
    """, (week_num,)).fetchall()

    analysts = db.execute("""
        SELECT id, equipo_favorito_id as fav, equipo_odia_id as hate
        FROM analysts ORDER BY id
    """).fetchall()

    picks: list[dict[str, Any]] = []
    for game in games:
        home, away = game["home_team_id"], game["away_team_id"]

        # --- Factor 2: Power rankings (0-1 scale) ---
        h_rank = rank_map.get(home, 5)
        a_rank = rank_map.get(away, 5)
        # Convert ranks to scores: rank 1 = 1.0, rank 8 = 0.0
        h_rank_score = (8 - h_rank) / 7 if rank_map else 0.5
        a_rank_score = (8 - a_rank) / 7 if rank_map else 0.5

        # --- Factor 3: Pitcher matchup (0-1 scale) ---
        h_pitch, _ = _get_best_available_pitcher(db, home, week_num)
        a_pitch, _ = _get_best_available_pitcher(db, away, week_num)
        max_pitch = max(h_pitch, a_pitch, 1)
        h_pitch_score = h_pitch / max_pitch
        a_pitch_score = a_pitch / max_pitch

        # --- Factor 4: Head-to-head (0-1 scale) ---
        h2h_hw, h2h_aw = _get_h2h_record(db, home, away)
        h2h_total = h2h_hw + h2h_aw
        h_h2h_score = h2h_hw / h2h_total if h2h_total else 0.5
        a_h2h_score = h2h_aw / h2h_total if h2h_total else 0.5

        for a in analysts:
            w = _ANALYST_WEIGHTS.get(a["id"], _ANALYST_WEIGHTS[1])

            # --- Factor 1: Favorite/hate bias (0-1 scale) ---
            # When fav is playing, always pick fav (1.0 vs 0.0)
            # When hate is playing (no fav), lean away from hate
            # When both fav AND hate play each other, fav gets max boost
            h_fav_score = 0.5
            a_fav_score = 0.5
            fav_in_game = a["fav"] in (home, away)
            hate_in_game = a["hate"] in (home, away)
            if fav_in_game:
                h_fav_score = 1.0 if a["fav"] == home else 0.0
                a_fav_score = 1.0 if a["fav"] == away else 0.0
            elif hate_in_game:
                h_fav_score = 0.15 if a["hate"] == home else 0.85
                a_fav_score = 0.15 if a["hate"] == away else 0.85

            # Weighted total
            h_total = (w["fav"] * h_fav_score + w["rank"] * h_rank_score
                       + w["pitch"] * h_pitch_score + w["h2h"] * h_h2h_score)
            a_total = (w["fav"] * a_fav_score + w["rank"] * a_rank_score
                       + w["pitch"] * a_pitch_score + w["h2h"] * a_h2h_score)

            pick = home if h_total >= a_total else away
            picks.append({
                "analyst_id": a["id"],
                "schedule_id": game["schedule_id"],
                "picked_team_id": pick,
                "week_num": week_num,
            })
    return picks


def save_game_picks(week_num: int, picks: list[dict[str, Any]]) -> None:
    """Save analyst game picks for a week. Clears existing picks first."""
    db = get_db()
    db.execute("DELETE FROM analyst_game_picks WHERE week_num = ?", (week_num,))
    for p in picks:
        db.execute("""
            INSERT INTO analyst_game_picks
                (analyst_id, schedule_id, picked_team_id, week_num)
            VALUES (?, ?, ?, ?)
        """, (p["analyst_id"], p["schedule_id"],
              p["picked_team_id"], p["week_num"]))
    db.commit()


def pick_game_of_week(week_num: int) -> int | None:
    """Pick the Game of the Week — closest matchup by power rankings.

    Scores each game: lower rank difference = more exciting.
    Tiebreak: higher combined ranking (both teams are good).
    """
    db = get_db()
    rank_map = _get_rank_map(week_num - 1) if week_num > 1 else {}
    if not rank_map:
        return None

    games = db.execute("""
        SELECT s.id as schedule_id, s.home_team_id, s.away_team_id
        FROM schedule s
        WHERE s.phase = 'regular' AND s.week_num = ?
        ORDER BY s.game_num
    """, (week_num,)).fetchall()

    if not games:
        return None

    best_id = None
    best_score = (-1, -1)
    for g in games:
        h_rank = rank_map.get(g["home_team_id"], 5)
        a_rank = rank_map.get(g["away_team_id"], 5)
        closeness = 8 - abs(h_rank - a_rank)  # closer = higher
        quality = 16 - (h_rank + a_rank)  # both top teams = higher
        score = (closeness, quality)
        if score > best_score:
            best_score = score
            best_id = g["schedule_id"]
    return best_id
