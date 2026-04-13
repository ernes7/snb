"""Shared standings service — used by main, teams, and playoffs."""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from typing import Any

from db import get_db


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
    Tiebreaker: 2-way tie uses head-to-head record; 3+ way tie uses run
    differential in games played among the tied teams.
    """
    db = get_db()
    teams = db.execute("SELECT * FROM teams").fetchall()
    owners = {t["id"]: t["owner"] for t in teams}
    standings: list[dict[str, Any]] = []

    for t in teams:
        row = dict(t)
        stats = db.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN (s.home_team_id=:tid AND g.home_runs>g.away_runs) OR
                    (s.away_team_id=:tid AND g.away_runs>g.home_runs) THEN 1 ELSE 0 END), 0) as wins,
                COALESCE(SUM(CASE WHEN (s.home_team_id=:tid AND g.home_runs<g.away_runs) OR
                    (s.away_team_id=:tid AND g.away_runs<g.home_runs) THEN 1 ELSE 0 END), 0) as losses,
                COALESCE(SUM(CASE WHEN s.home_team_id=:tid THEN g.home_runs
                    WHEN s.away_team_id=:tid THEN g.away_runs ELSE 0 END), 0) as rs,
                COALESCE(SUM(CASE WHEN s.home_team_id=:tid THEN g.away_runs
                    WHEN s.away_team_id=:tid THEN g.home_runs ELSE 0 END), 0) as ra
            FROM games g JOIN schedule s ON g.schedule_id=s.id
            WHERE s.phase='regular' AND (s.home_team_id=:tid OR s.away_team_id=:tid)
        """, {"tid": t['id']}).fetchone()

        row['wins'] = stats['wins']
        row['losses'] = stats['losses']
        total = stats['wins'] + stats['losses']
        row['_pct'] = stats['wins'] / total if total > 0 else 0.0
        row['pct'] = f"{row['_pct']:.3f}" if total > 0 else ".000"
        row['rs'] = stats['rs']
        row['ra'] = stats['ra']
        row['diff'] = stats['rs'] - stats['ra']
        standings.append(row)

    # Load every played regular-season game once for tiebreaker math
    games = db.execute("""
        SELECT s.home_team_id AS h, s.away_team_id AS a,
               g.home_runs AS hr, g.away_runs AS ar
        FROM games g JOIN schedule s ON g.schedule_id=s.id
        WHERE s.phase='regular' AND g.home_runs IS NOT NULL
    """).fetchall()

    # Bucket by win%, compute in-group tiebreaker for every multi-team bucket
    groups: dict[float, list[int]] = defaultdict(list)
    for s in standings:
        groups[s['_pct']].append(s['id'])

    tb: dict[int, tuple[int, int]] = {s['id']: (0, 0) for s in standings}
    for pct, ids in groups.items():
        if len(ids) > 1:
            tb.update(_tiebreak_values(ids, games, owners))

    for s in standings:
        s['_tb1'], s['_tb2'] = tb[s['id']]

    standings.sort(
        key=lambda x: (-x['_pct'], -x['_tb1'], -x['_tb2'], -x['diff'], x['id'])
    )

    if standings and (standings[0]['wins'] + standings[0]['losses']) > 0:
        top = standings[0]['wins'] - standings[0]['losses']
        for s in standings:
            diff = top - (s['wins'] - s['losses'])
            s['gb'] = '-' if diff == 0 else f"{diff/2:.1f}"
    else:
        for s in standings:
            s['gb'] = '-'

    for s in standings:
        s.pop('_pct', None)
        s.pop('_tb1', None)
        s.pop('_tb2', None)

    return standings


def get_all_teams() -> list[sqlite3.Row]:
    """Get all teams ordered by name."""
    return get_db().execute("SELECT * FROM teams ORDER BY name").fetchall()
