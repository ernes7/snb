"""League standings computation — model-backed.

`Team.records_all()` gives us every team's W/L/RS/RA in one query.
Tiebreaker math still needs raw per-game data (games among tied teams),
which is loaded once here. The per-team query loop this file used to
run (8 separate SELECTs) is gone.
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from typing import Any

from db import get_db
from lib.season import Phase
from models import Team
from models.team import TeamRecord


def _tiebreak_values(
    tied_ids: list[int],
    games: list[sqlite3.Row],
    owners: dict[int, str],
) -> dict[int, tuple[int, int]]:
    """Compute the in-group tiebreaker for a set of tied teams.

    Returns `{team_id: (primary, secondary)}` — both higher-is-better,
    lexicographic order.

    **2-team tie**: primary = head-to-head wins, secondary = run
    differential in those H2H games. If both teams share an owner
    (same-owner teams never face each other in this league), return
    zeros so the sort falls through to overall run diff.

    **3+ team tie**: primary = run differential restricted to games
    played among the tied teams only; secondary = 0. Same-owner pairs
    within the group naturally contribute no intra-group games.
    """
    if len(tied_ids) == 2:
        a, b = tied_ids
        if owners.get(a) == owners.get(b):
            return {a: (0, 0), b: (0, 0)}
        wins = {a: 0, b: 0}
        diffs = {a: 0, b: 0}
        pair = {a, b}
        for g in games:
            if {g["h"], g["a"]} != pair:
                continue
            margin = g["hr"] - g["ar"]
            diffs[g["h"]] += margin
            diffs[g["a"]] -= margin
            if margin > 0:
                wins[g["h"]] += 1
            elif margin < 0:
                wins[g["a"]] += 1
        return {a: (wins[a], diffs[a]), b: (wins[b], diffs[b])}
    gset = set(tied_ids)
    intra: dict[int, int] = {tid: 0 for tid in tied_ids}
    for g in games:
        if g["h"] in gset and g["a"] in gset:
            intra[g["h"]] += g["hr"] - g["ar"]
            intra[g["a"]] += g["ar"] - g["hr"]
    return {tid: (intra[tid], 0) for tid in tied_ids}


def get_standings() -> list[dict[str, Any]]:
    """Compute league standings with tiebreakers.

    Sort order: win% desc → in-group tiebreaker desc → overall run diff desc.
    Output shape: list of dicts with every `teams` column plus
    `wins, losses, pct, rs, ra, diff, gb` — consumed by templates as
    `stats.wins` / `stats.pct` / etc.
    """
    records = Team.records_all(phase=Phase.REGULAR)
    teams = Team.all()
    owners = {t.id: t.owner for t in teams}

    standings: list[dict[str, Any]] = []
    for t in teams:
        rec = records.get(t.id) or TeamRecord(0, 0, 0, 0)
        row = dict(t.row)
        row.update({
            "wins": rec.wins,
            "losses": rec.losses,
            "_pct": rec.pct_float,
            "pct": rec.pct,
            "rs": rec.rs,
            "ra": rec.ra,
            "diff": rec.diff,
        })
        standings.append(row)

    # Per-game data for tiebreakers — one query, one pass.
    games = get_db().execute("""
        SELECT s.home_team_id AS h, s.away_team_id AS a,
               g.home_runs AS hr, g.away_runs AS ar
        FROM games g JOIN schedule s ON g.schedule_id = s.id
        WHERE s.phase = ? AND g.home_runs IS NOT NULL
    """, (Phase.REGULAR,)).fetchall()

    groups: dict[float, list[int]] = defaultdict(list)
    for s in standings:
        groups[s["_pct"]].append(s["id"])

    tb: dict[int, tuple[int, int]] = {s["id"]: (0, 0) for s in standings}
    for _pct, ids in groups.items():
        if len(ids) > 1:
            tb.update(_tiebreak_values(ids, games, owners))

    for s in standings:
        s["_tb1"], s["_tb2"] = tb[s["id"]]

    standings.sort(
        key=lambda x: (-x["_pct"], -x["_tb1"], -x["_tb2"], -x["diff"], x["id"])
    )

    if standings and (standings[0]["wins"] + standings[0]["losses"]) > 0:
        top = standings[0]["wins"] - standings[0]["losses"]
        for s in standings:
            diff = top - (s["wins"] - s["losses"])
            s["gb"] = "-" if diff == 0 else f"{diff/2:.1f}"
    else:
        for s in standings:
            s["gb"] = "-"

    for s in standings:
        s.pop("_pct", None)
        s.pop("_tb1", None)
        s.pop("_tb2", None)

    return standings


