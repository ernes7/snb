"""Deterministic power rankings computation."""
from __future__ import annotations

import json
from typing import Any

from db import get_db


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
    team_ids = [r["id"] for r in db.execute(
        "SELECT id FROM teams ORDER BY id"
    ).fetchall()]

    # --- Query 1: Overall W/L/RS/RA through week_num ---
    records = db.execute("""
        SELECT t.id as team_id,
            COALESCE(SUM(CASE WHEN (s.home_team_id=t.id AND g.home_runs>g.away_runs)
                OR (s.away_team_id=t.id AND g.away_runs>g.home_runs) THEN 1 ELSE 0 END), 0) as wins,
            COALESCE(SUM(CASE WHEN (s.home_team_id=t.id AND g.home_runs<g.away_runs)
                OR (s.away_team_id=t.id AND g.away_runs<g.home_runs) THEN 1 ELSE 0 END), 0) as losses,
            COALESCE(SUM(CASE WHEN s.home_team_id=t.id THEN g.home_runs
                WHEN s.away_team_id=t.id THEN g.away_runs ELSE 0 END), 0) as rs,
            COALESCE(SUM(CASE WHEN s.home_team_id=t.id THEN g.away_runs
                WHEN s.away_team_id=t.id THEN g.home_runs ELSE 0 END), 0) as ra,
            COUNT(g.id) as gp
        FROM teams t
        LEFT JOIN schedule s ON (s.home_team_id=t.id OR s.away_team_id=t.id)
            AND s.phase='regular' AND s.week_num <= ?
        LEFT JOIN games g ON g.schedule_id=s.id
        GROUP BY t.id
    """, (week_num,)).fetchall()
    rec = {r["team_id"]: dict(r) for r in records}

    # --- Query 2: Recent 5-week W/L ---
    recent_start = max(1, week_num - 4)
    recent = db.execute("""
        SELECT t.id as team_id,
            COALESCE(SUM(CASE WHEN (s.home_team_id=t.id AND g.home_runs>g.away_runs)
                OR (s.away_team_id=t.id AND g.away_runs>g.home_runs) THEN 1 ELSE 0 END), 0) as wins,
            COALESCE(SUM(CASE WHEN (s.home_team_id=t.id AND g.home_runs<g.away_runs)
                OR (s.away_team_id=t.id AND g.away_runs<g.home_runs) THEN 1 ELSE 0 END), 0) as losses
        FROM teams t
        LEFT JOIN schedule s ON (s.home_team_id=t.id OR s.away_team_id=t.id)
            AND s.phase='regular' AND s.week_num BETWEEN ? AND ?
        LEFT JOIN games g ON g.schedule_id=s.id
        GROUP BY t.id
    """, (recent_start, week_num)).fetchall()
    rec_recent = {r["team_id"]: dict(r) for r in recent}

    # --- Query 3: Team batting aggregates ---
    batting = db.execute("""
        SELECT bs.team_id,
            SUM(bs.AB) as AB, SUM(bs.H) as H, SUM(bs.HR) as HR, SUM(bs.RBI) as RBI
        FROM batting_stats bs
        JOIN games g ON bs.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        WHERE s.phase='regular' AND s.week_num <= ?
        GROUP BY bs.team_id
    """, (week_num,)).fetchall()
    bat = {r["team_id"]: dict(r) for r in batting}

    # --- Query 4: Team pitching aggregates ---
    pitching = db.execute("""
        SELECT ps.team_id,
            SUM(ps.IP_outs) as IP_outs, SUM(ps.ER) as ER, SUM(ps.SO) as SO
        FROM pitching_stats ps
        JOIN games g ON ps.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        WHERE s.phase='regular' AND s.week_num <= ?
        GROUP BY ps.team_id
    """, (week_num,)).fetchall()
    pit = {r["team_id"]: dict(r) for r in pitching}

    # --- Query 5: Matchups for strength of schedule ---
    matchups = db.execute("""
        SELECT s.home_team_id, s.away_team_id
        FROM schedule s JOIN games g ON g.schedule_id = s.id
        WHERE s.phase='regular' AND s.week_num <= ?
    """, (week_num,)).fetchall()

    # Build raw metrics per team
    raw: dict[int, dict[str, float]] = {}
    for tid in team_ids:
        r = rec.get(tid, {"wins": 0, "losses": 0, "rs": 0, "ra": 0, "gp": 0})
        gp = max(r["gp"], 1)
        win_pct = r["wins"] / max(r["wins"] + r["losses"], 1)

        rr = rec_recent.get(tid, {"wins": 0, "losses": 0})
        recent_pct = rr["wins"] / max(rr["wins"] + rr["losses"], 1)

        run_diff = (r["rs"] - r["ra"]) / gp

        b = bat.get(tid, {"AB": 0, "H": 0, "HR": 0, "RBI": 0})
        ab = max(b["AB"], 1)
        avg = b["H"] / ab
        hr_rate = b["HR"] / ab
        rbi_rate = b["RBI"] / ab

        p = pit.get(tid, {"IP_outs": 0, "ER": 0, "SO": 0})
        ip_outs = max(p["IP_outs"], 1)
        era = (p["ER"] * 27) / ip_outs  # 9 innings = 27 outs
        era_inv = 1.0 / max(era, 0.50)
        so_rate = p["SO"] / ip_outs

        # SOS: average win% of opponents faced
        opp_pcts: list[float] = []
        for m in matchups:
            if m["home_team_id"] == tid:
                opp = rec.get(m["away_team_id"], {"wins": 0, "losses": 0})
                opp_pcts.append(opp["wins"] / max(opp["wins"] + opp["losses"], 1))
            elif m["away_team_id"] == tid:
                opp = rec.get(m["home_team_id"], {"wins": 0, "losses": 0})
                opp_pcts.append(opp["wins"] / max(opp["wins"] + opp["losses"], 1))
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
    WEIGHTS = {
        "win_pct": 0.10, "recent": 0.19, "run_diff": 0.14,
        "batting": 0.19, "pitching": 0.19, "sos": 0.19,
    }
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
