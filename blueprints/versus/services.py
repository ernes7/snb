"""Versus service — head-to-head matrix and per-team split stats."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from db import get_db


def _parse_linescore(s: str | None) -> list[int]:
    """Parse "1,0,1,0,0,0,2,0,1" → [1,0,1,0,0,0,2,0,1]. Empty/None → []."""
    if not s:
        return []
    return [int(x) for x in s.split(",") if x.strip()]


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


def build_versus_page() -> dict[str, Any]:
    """Compose all data needed by the /versus page."""
    return {
        **build_versus_matrix(),
        "splits": get_split_records(),
        "inning_diff": get_inning_differential(),
    }
