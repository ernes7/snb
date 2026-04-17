"""Deterministic power rankings computation."""
from __future__ import annotations

import json
from typing import Any

from db import get_db
from lib.scoring import POWER_RANKING_WEIGHTS, RECENT_FORM_LOOKBACK_WEEKS
from lib.season import Phase
from models import Team


def _min_max(values: list[float]) -> list[float]:
    """Min-max normalize a list of floats to [0, 1]."""
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def compute_power_rankings(week_num: int) -> list[dict[str, Any]]:
    """Compute deterministic power rankings for a given week.

    Returns list of dicts sorted by rank ascending, each containing:
        team_id, rank, prev_rank, score, and per-component weighted scores.

    Formula weights:
        Overall win %:       10%
        Recent 5-week win %: 19%
        Run differential/gm: 14%
        Batting composite:   19%  (AVG, HR/AB, RBI/AB)
        Pitching composite:  19%  (ERA_inv, SO/IP)
        Strength of schedule:19%
    """
    db = get_db()
    team_ids = [t.id for t in Team.all()]

    # --- Team records (overall + recent form) via Team model batch methods
    rec = Team.records_all(through_week=week_num, phase=Phase.REGULAR)
    recent_start = max(1, week_num - (RECENT_FORM_LOOKBACK_WEEKS - 1))
    rec_recent = Team.records_for_weeks(recent_start, week_num, phase=Phase.REGULAR)

    # --- Team batting/pitching aggregates via Team.team_stats_all
    bat_lines, pit_lines = Team.team_stats_all(
        through_week=week_num, phase=Phase.REGULAR,
    )

    # --- Matchups for strength of schedule (opponent-relative, no shared shape)
    matchups = db.execute("""
        SELECT s.home_team_id, s.away_team_id
        FROM schedule s JOIN games g ON g.schedule_id = s.id
        WHERE s.phase = ? AND s.week_num <= ?
    """, (Phase.REGULAR, week_num)).fetchall()

    # Build raw metrics per team
    raw: dict[int, dict[str, float]] = {}
    for tid in team_ids:
        tr = rec.get(tid)
        gp = max(tr.games, 1) if tr else 1
        win_pct = tr.pct_float if tr else 0.0

        rr = rec_recent.get(tid)
        recent_pct = rr.pct_float if rr else 0.0

        run_diff = tr.diff / gp if tr else 0.0

        bl = bat_lines.get(tid)
        ab = max(bl.AB, 1) if bl else 1
        avg = bl.AVG if bl else 0.0
        hr_rate = (bl.HR / ab) if bl else 0.0
        rbi_rate = (bl.RBI / ab) if bl else 0.0

        pl = pit_lines.get(tid)
        ip_outs = max(pl.IP_outs, 1) if pl else 1
        era = pl.ERA if pl else 0.0
        era_inv = 1.0 / max(era, 0.50)
        so_rate = (pl.SO / ip_outs) if pl else 0.0

        # SOS: average win% of opponents faced
        opp_pcts: list[float] = []
        for m in matchups:
            opp_id = None
            if m["home_team_id"] == tid:
                opp_id = m["away_team_id"]
            elif m["away_team_id"] == tid:
                opp_id = m["home_team_id"]
            if opp_id is not None:
                opp = rec.get(opp_id)
                opp_pcts.append(opp.pct_float if opp else 0.0)
        sos = sum(opp_pcts) / max(len(opp_pcts), 1)

        raw[tid] = {
            "win_pct": win_pct, "recent_pct": recent_pct, "run_diff": run_diff,
            "avg": avg, "hr_rate": hr_rate, "rbi_rate": rbi_rate,
            "era_inv": era_inv, "so_rate": so_rate, "sos": sos,
        }

    # Min-max normalize each component across all 8 teams
    order = sorted(team_ids)
    norm_win = _min_max([raw[t]["win_pct"] for t in order])
    norm_recent = _min_max([raw[t]["recent_pct"] for t in order])
    norm_rd = _min_max([raw[t]["run_diff"] for t in order])
    norm_avg = _min_max([raw[t]["avg"] for t in order])
    norm_hr = _min_max([raw[t]["hr_rate"] for t in order])
    norm_rbi = _min_max([raw[t]["rbi_rate"] for t in order])
    norm_era = _min_max([raw[t]["era_inv"] for t in order])
    norm_so = _min_max([raw[t]["so_rate"] for t in order])
    norm_sos = _min_max([raw[t]["sos"] for t in order])

    # Weighted composite score with per-component breakdown
    WEIGHTS = POWER_RANKING_WEIGHTS
    scores: dict[int, float] = {}
    components: dict[int, dict[str, float]] = {}
    for i, tid in enumerate(order):
        bat_comp = (norm_avg[i] + norm_hr[i] + norm_rbi[i]) / 3
        pit_comp = (norm_era[i] + norm_so[i]) / 2
        c = {
            "win_pct": WEIGHTS["win_pct"] * norm_win[i],
            "recent": WEIGHTS["recent"] * norm_recent[i],
            "run_diff": WEIGHTS["run_diff"] * norm_rd[i],
            "batting": WEIGHTS["batting"] * bat_comp,
            "pitching": WEIGHTS["pitching"] * pit_comp,
            "sos": WEIGHTS["sos"] * norm_sos[i],
        }
        scores[tid] = sum(c.values())
        components[tid] = c

    # Sort by score desc; tiebreak: win_pct, run_diff, team_id
    ranked = sorted(
        order,
        key=lambda t: (scores[t], raw[t]["win_pct"], raw[t]["run_diff"], -t),
        reverse=True,
    )

    # Load previous week's rankings for prev_rank
    prev_rank_map: dict[int, int] = {}
    if week_num > 1:
        prev = db.execute(
            "SELECT power_rankings FROM weekly_awards WHERE week_num = ?",
            (week_num - 1,),
        ).fetchone()
        if prev and prev["power_rankings"]:
            for entry in json.loads(prev["power_rankings"]):
                prev_rank_map[entry["team_id"]] = entry["rank"]

    result = []
    for rank, tid in enumerate(ranked, 1):
        result.append({
            "team_id": tid,
            "rank": rank,
            "prev_rank": prev_rank_map.get(tid),
            "score": round(scores[tid], 4),
            "components": {k: round(v, 4) for k, v in components[tid].items()},
        })
    return result
