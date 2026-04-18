"""Weekly summary and awards services."""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from db import get_db
from lib.season import Phase, week_game_range
from lib.scoring import (
    ANALYST_WEIGHTS,
    GOTW_QUALITY_WEIGHT,
    HATE_BIAS_BOOST,
    HATE_BIAS_PENALTY,
)
from lib.utils import format_ip


def get_week_games(week_num: int) -> list[dict]:
    """Get all game results for a given week (4 games per week).

    Delegates to the shared `models.game.week_games` helper so the same
    query + pitcher-credit rollup is used by both weekly and main pages.
    """
    from models.game import week_games
    return week_games(week_num)


def get_week_top_batters(week_num: int, limit: int = 5) -> list[sqlite3.Row]:
    """Top batters for the week by a composite score (H + 2*HR + RBI)."""
    db = get_db()
    start, end = week_game_range(week_num)
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
    start, end = week_game_range(week_num)
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
        "DELETE FROM analyst_tweets WHERE week_num = ? AND game_id IS NULL",
        (week_num,)
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
        WHERE at.week_num = ? AND at.game_id IS NULL
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
            w = ANALYST_WEIGHTS.get(a["id"], ANALYST_WEIGHTS[1])

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
                h_fav_score = HATE_BIAS_PENALTY if a["hate"] == home else HATE_BIAS_BOOST
                a_fav_score = HATE_BIAS_PENALTY if a["hate"] == away else HATE_BIAS_BOOST

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
    """Pick the Game of the Week — best combination of quality and closeness.

    Scoring: quality (both teams near top) dominates, closeness is a bonus.
    A 1-vs-2 matchup beats 7-vs-8 even though both are "close", and a
    top-team-vs-mid-team beats a close mid-vs-mid matchup.

        closeness_bonus = 8 - abs(h_rank - a_rank)   # 0-7
        quality_bonus   = 16 - (h_rank + a_rank)     # 0-14
        score           = quality_bonus * 3 + closeness_bonus
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
    best_score = -1
    for g in games:
        h_rank = rank_map.get(g["home_team_id"], 5)
        a_rank = rank_map.get(g["away_team_id"], 5)
        closeness_bonus = 8 - abs(h_rank - a_rank)
        quality_bonus = 16 - (h_rank + a_rank)
        score = quality_bonus * GOTW_QUALITY_WEIGHT + closeness_bonus
        if score > best_score:
            best_score = score
            best_id = g["schedule_id"]
    return best_id


def save_game_of_week(week_num: int) -> int | None:
    """Compute the Game of the Week for `week_num` and persist it.

    Returns the schedule_id stored (or None if no ranking data yet — e.g.
    calling this before any prior week has rankings).
    """
    gotw_id = pick_game_of_week(week_num)
    if gotw_id is None:
        return None
    db = get_db()
    db.execute("""
        INSERT INTO weekly_awards (week_num, game_of_week_id) VALUES (?, ?)
        ON CONFLICT(week_num) DO UPDATE SET game_of_week_id = excluded.game_of_week_id
    """, (week_num, gotw_id))
    db.commit()
    return gotw_id


def week_completion_status(week_num: int) -> dict[str, Any]:
    """Return how many games in a week have been played and box scored.

    A game counts as "played" when a row exists in games with both scores.
    A game counts as "boxscored" when it also has batting_stats entries.
    """
    db = get_db()
    total = db.execute(
        "SELECT COUNT(*) FROM schedule WHERE phase='regular' AND week_num=?",
        (week_num,),
    ).fetchone()[0]
    played = db.execute("""
        SELECT COUNT(*) FROM games g
        JOIN schedule s ON g.schedule_id = s.id
        WHERE s.phase='regular' AND s.week_num=?
          AND g.home_runs IS NOT NULL AND g.away_runs IS NOT NULL
    """, (week_num,)).fetchone()[0]
    boxscored = db.execute("""
        SELECT COUNT(DISTINCT g.id) FROM games g
        JOIN schedule s ON g.schedule_id = s.id
        JOIN batting_stats bs ON bs.game_id = g.id
        WHERE s.phase='regular' AND s.week_num=?
    """, (week_num,)).fetchone()[0]
    return {"total": total, "played": played, "boxscored": boxscored}


def can_auto_generate(week_num: int) -> tuple[bool, str]:
    """Check if auto-generation is allowed for the given target week.

    Guards:
      1. The previous week (week_num - 1) must have all games fully box scored.
      2. The target week (week_num) must have zero games played.

    Returns (allowed, reason_if_denied).
    """
    if week_num < 2:
        return False, "La primera semana no tiene semana previa para rankings."

    prev = week_completion_status(week_num - 1)
    if prev["total"] == 0:
        return False, f"La semana {week_num - 1} no existe."
    if prev["boxscored"] < prev["total"]:
        return False, (
            f"La semana {week_num - 1} aun no esta completa "
            f"({prev['boxscored']}/{prev['total']} juegos con box score)."
        )

    curr = week_completion_status(week_num)
    if curr["total"] == 0:
        return False, f"La semana {week_num} no existe."
    if curr["played"] > 0:
        return False, (
            f"La semana {week_num} ya tiene juegos jugados "
            f"({curr['played']}/{curr['total']}); no se puede regenerar."
        )

    return True, ""


def auto_generate_week(week_num: int) -> dict[str, Any]:
    """Auto-generate deterministic weekly content for `week_num`.

    Runs the three pure-logic steps that do not require Claude:
      1. Compute power rankings using data through week_num - 1
         and upsert into weekly_awards[week_num - 1] (preserving any
         POTW/summary/game_of_week_id already set).
      2. Generate and save analyst game picks for week_num.
      3. Pick the Game of the Week for week_num and store it in
         weekly_awards[week_num].game_of_week_id.

    Note: per-team ranking comments and POTW summary remain blank —
    those are Claude's creative contribution, filled in later.

    Raises ValueError if guards fail. Returns a summary dict.
    """
    from services.power_rankings import compute_power_rankings

    allowed, reason = can_auto_generate(week_num)
    if not allowed:
        raise ValueError(reason)

    db = get_db()

    # 1. Rankings for week_num - 1 — preserve any existing blurbs by team_id
    prev_week = week_num - 1
    rankings = compute_power_rankings(prev_week)
    existing = db.execute(
        "SELECT power_rankings FROM weekly_awards WHERE week_num = ?",
        (prev_week,),
    ).fetchone()
    if existing and existing["power_rankings"]:
        prior_blurbs = {
            r["team_id"]: r.get("blurb")
            for r in json.loads(existing["power_rankings"])
        }
        for r in rankings:
            if prior_blurbs.get(r["team_id"]):
                r["blurb"] = prior_blurbs[r["team_id"]]
    db.execute("""
        INSERT INTO weekly_awards (week_num, power_rankings)
        VALUES (?, ?)
        ON CONFLICT(week_num) DO UPDATE SET
            power_rankings = excluded.power_rankings
    """, (prev_week, json.dumps(rankings)))

    # 2. Game picks for week_num
    picks = generate_game_picks(week_num)
    save_game_picks(week_num, picks)

    # 3. Game of the Week for week_num → stored on its own row
    gotw_id = pick_game_of_week(week_num)
    if gotw_id is not None:
        db.execute("""
            INSERT INTO weekly_awards (week_num, game_of_week_id)
            VALUES (?, ?)
            ON CONFLICT(week_num) DO UPDATE SET
                game_of_week_id = excluded.game_of_week_id
        """, (week_num, gotw_id))

    db.commit()

    return {
        "week_num": week_num,
        "prev_week": prev_week,
        "rankings_count": len(rankings),
        "picks_count": len(picks),
        "game_of_week_id": gotw_id,
    }


def save_game_tweets(
    game_id: int,
    tweets: list[dict[str, Any]],
) -> None:
    """Save analyst tweets + fan replies for a game. Likes are auto-randomized.

    Args:
        game_id: The game ID from the games table.
        tweets: List of dicts, each with:
            - analyst_id: int
            - texto: str (the tweet text, include hashtag)
            - replies: list of {commenter_id: int, texto: str}
    """
    import random
    db = get_db()

    week = db.execute("""
        SELECT s.week_num FROM games g
        JOIN schedule s ON g.schedule_id = s.id
        WHERE g.id = ?
    """, (game_id,)).fetchone()
    week_num = week["week_num"] if week else None

    for t in tweets:
        likes = random.randint(15, 120)
        cursor = db.execute("""
            INSERT INTO analyst_tweets (analyst_id, game_id, texto, week_num, likes)
            VALUES (?, ?, ?, ?, ?)
        """, (t["analyst_id"], game_id, t["texto"], week_num, likes))
        tweet_id = cursor.lastrowid

        for r in t.get("replies", []):
            reply_likes = random.randint(2, 45)
            db.execute("""
                INSERT INTO tweet_replies (tweet_id, commenter_id, texto, likes)
                VALUES (?, ?, ?, ?)
            """, (tweet_id, r["commenter_id"], r["texto"], reply_likes))

    db.commit()


def get_prediction_records() -> list[dict[str, Any]]:
    """Get each analyst's prediction accuracy across all played games.

    Returns list sorted by correct count descending:
        [{analyst_id, handle, avatar_file, emoji, correct, total, pct}]
    """
    db = get_db()
    rows = db.execute("""
        SELECT a.id as analyst_id, a.handle, a.avatar_file, a.emoji,
            COUNT(p.id) as total,
            SUM(CASE
                WHEN (s.home_team_id = p.picked_team_id AND g.home_runs > g.away_runs)
                  OR (s.away_team_id = p.picked_team_id AND g.away_runs > g.home_runs)
                THEN 1 ELSE 0
            END) as correct
        FROM analyst_game_picks p
        JOIN analysts a ON p.analyst_id = a.id
        JOIN schedule s ON p.schedule_id = s.id
        JOIN games g ON g.schedule_id = s.id
        GROUP BY a.id
        ORDER BY correct DESC, total ASC
    """).fetchall()
    return [{
        **dict(r),
        "pct": round(r["correct"] / r["total"] * 100, 1) if r["total"] else 0,
    } for r in rows]
