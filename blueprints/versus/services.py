"""Versus service — head-to-head matrix and per-team split stats."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from db import get_db


def _parse_linescore(s: str | None) -> list[int]:
    """Parse "1,0,1,0,0,0,2,0,1" → [1,0,1,0,0,0,2,0,1]. Empty/None → []."""
    if not s:
        return []
    return [int(x) for x in s.split(",") if x.strip() and x.strip() != "X"]


def build_versus_matrix() -> dict[str, Any]:
    """Return teams (owner-grouped) and a dict keyed by (row_id, col_id) → {w, l}.

    Only regular-season completed games are counted. Same-owner pairs never
    play each other, so those keys will be absent from the matrix.
    """
    db = get_db()
    teams = db.execute(
        "SELECT * FROM teams ORDER BY owner, short_name"
    ).fetchall()

    games = db.execute("""
        SELECT s.home_team_id AS h, s.away_team_id AS a,
               g.home_runs AS hr, g.away_runs AS ar
        FROM games g JOIN schedule s ON g.schedule_id=s.id
        WHERE s.phase='regular' AND g.home_runs IS NOT NULL
    """).fetchall()

    matrix: dict[tuple[int, int], dict[str, int]] = defaultdict(
        lambda: {"w": 0, "l": 0}
    )
    for g in games:
        if g["hr"] > g["ar"]:
            winner, loser = g["h"], g["a"]
        elif g["ar"] > g["hr"]:
            winner, loser = g["a"], g["h"]
        else:
            continue
        matrix[(winner, loser)]["w"] += 1
        matrix[(loser, winner)]["l"] += 1

    return {"teams": teams, "matrix": dict(matrix)}


def _first_scorer(home_ls: list[int], away_ls: list[int]) -> str | None:
    """Return 'home', 'away', or None based on which team scored first.

    Away bats top of each inning, so within inning i: if away_ls[i] > 0, away
    scored first; otherwise if home_ls[i] > 0, home scored first.
    """
    n = max(len(home_ls), len(away_ls))
    for i in range(n):
        a = away_ls[i] if i < len(away_ls) else 0
        h = home_ls[i] if i < len(home_ls) else 0
        if a > 0:
            return "away"
        if h > 0:
            return "home"
    return None


def get_split_records() -> list[dict[str, Any]]:
    """Per-team W-L in (a) 1-run games and (b) games where team scored first.

    Returns list sorted by 1-run wins desc, 1-run losses asc, short_name.
    """
    db = get_db()
    teams = db.execute("SELECT * FROM teams").fetchall()
    rec: dict[int, dict[str, Any]] = {}
    for t in teams:
        rec[t["id"]] = {
            "id": t["id"],
            "short_name": t["short_name"],
            "name": t["name"],
            "color_primary": t["color_primary"],
            "logo_file": t["logo_file"],
            "owner": t["owner"],
            "close_w": 0, "close_l": 0,
            "first_w": 0, "first_l": 0,
        }

    games = db.execute("""
        SELECT s.home_team_id AS h, s.away_team_id AS a,
               g.home_runs AS hr, g.away_runs AS ar,
               g.home_linescore AS hls, g.away_linescore AS als
        FROM games g JOIN schedule s ON g.schedule_id=s.id
        WHERE s.phase='regular' AND g.home_runs IS NOT NULL
    """).fetchall()

    for g in games:
        winner, loser = (g["h"], g["a"]) if g["hr"] > g["ar"] else (g["a"], g["h"])

        # 1-run game split
        if abs(g["hr"] - g["ar"]) == 1:
            rec[winner]["close_w"] += 1
            rec[loser]["close_l"] += 1

        # Scoring-first split
        first = _first_scorer(_parse_linescore(g["hls"]), _parse_linescore(g["als"]))
        if first is None:
            continue
        scorer = g["h"] if first == "home" else g["a"]
        if scorer == winner:
            rec[scorer]["first_w"] += 1
        else:
            rec[scorer]["first_l"] += 1

    out = list(rec.values())
    out.sort(key=lambda r: (-r["close_w"], r["close_l"], r["short_name"]))
    return out


def get_inning_differential() -> dict[int, list[int]]:
    """Per-team run differential by inning (index 0..8 = innings 1..9).

    Parses `home_linescore` / `away_linescore` from every completed regular-
    season game. Mercy-rule games with shorter linescores are zero-padded.
    """
    db = get_db()
    team_ids = [r["id"] for r in db.execute("SELECT id FROM teams").fetchall()]
    diff: dict[int, list[int]] = {tid: [0] * 9 for tid in team_ids}

    rows = db.execute("""
        SELECT s.home_team_id AS h, s.away_team_id AS a,
               g.home_linescore AS hls, g.away_linescore AS als
        FROM games g JOIN schedule s ON g.schedule_id=s.id
        WHERE s.phase='regular' AND g.home_runs IS NOT NULL
    """).fetchall()

    for r in rows:
        home_ls = _parse_linescore(r["hls"])
        away_ls = _parse_linescore(r["als"])
        for i in range(9):
            h = home_ls[i] if i < len(home_ls) else 0
            a = away_ls[i] if i < len(away_ls) else 0
            diff[r["h"]][i] += h - a
            diff[r["a"]][i] += a - h

    return diff


def build_matchup_page(team_a, team_b) -> dict[str, Any]:
    """Return played games (with parsed linescores), upcoming schedule,
    and H2H record for two teams."""
    db = get_db()
    a_id, b_id = team_a.id, team_b.id

    played_rows = db.execute("""
        SELECT g.id, s.game_num, s.week_num,
               s.home_team_id, s.away_team_id,
               g.home_runs, g.away_runs, g.home_hits, g.away_hits,
               g.home_errors, g.away_errors,
               g.home_linescore, g.away_linescore,
               wp.name AS wp_name, lp.name AS lp_name, sp.name AS sv_name
        FROM games g
        JOIN schedule s ON g.schedule_id = s.id
        LEFT JOIN players wp ON g.winning_pitcher_id = wp.id
        LEFT JOIN players lp ON g.losing_pitcher_id = lp.id
        LEFT JOIN players sp ON g.save_pitcher_id = sp.id
        WHERE s.phase = 'regular'
          AND ((s.home_team_id = ? AND s.away_team_id = ?)
            OR (s.home_team_id = ? AND s.away_team_id = ?))
          AND g.home_runs IS NOT NULL
        ORDER BY s.game_num
    """, (a_id, b_id, b_id, a_id)).fetchall()

    teams_by_id = {team_a.id: team_a, team_b.id: team_b}
    played = []
    for r in played_rows:
        home = teams_by_id[r["home_team_id"]]
        away = teams_by_id[r["away_team_id"]]
        home_ls = _parse_linescore(r["home_linescore"])
        away_ls = _parse_linescore(r["away_linescore"])
        innings = max(len(home_ls), len(away_ls), 9)
        played.append({
            "game_num": r["game_num"], "week_num": r["week_num"],
            "home": home, "away": away,
            "home_ls": home_ls, "away_ls": away_ls,
            "home_runs": r["home_runs"], "away_runs": r["away_runs"],
            "home_hits": r["home_hits"], "away_hits": r["away_hits"],
            "home_errors": r["home_errors"], "away_errors": r["away_errors"],
            "innings": innings,
            "wp_name": r["wp_name"], "lp_name": r["lp_name"],
            "sv_name": r["sv_name"],
        })

    upcoming_rows = db.execute("""
        SELECT s.game_num, s.week_num, s.home_team_id, s.away_team_id
        FROM schedule s
        LEFT JOIN games g ON g.schedule_id = s.id
        WHERE s.phase = 'regular'
          AND ((s.home_team_id = ? AND s.away_team_id = ?)
            OR (s.home_team_id = ? AND s.away_team_id = ?))
          AND g.id IS NULL
        ORDER BY s.game_num
    """, (a_id, b_id, b_id, a_id)).fetchall()

    upcoming = []
    for r in upcoming_rows:
        upcoming.append({
            "game_num": r["game_num"], "week_num": r["week_num"],
            "home": teams_by_id[r["home_team_id"]],
            "away": teams_by_id[r["away_team_id"]],
        })

    return {
        "team_a": team_a, "team_b": team_b,
        "h2h": team_a.h2h_vs(team_b),
        "played": played, "upcoming": upcoming,
    }


def build_versus_page() -> dict[str, Any]:
    """Compose all data needed by the /versus page."""
    return {
        **build_versus_matrix(),
        "splits": get_split_records(),
        "inning_diff": get_inning_differential(),
    }
