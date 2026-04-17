"""Additional MVP awards beyond Kindelan (batter) and Lazo (starter).

Four awards live here — each reuses `RaceEntry` / `CategoryBonus` from
`services.py` and the team multiplier from `lib/scoring.py`, but each
has its own scoring mechanic:

- `compute_artesano_race` — starter Cy Young by Bill James game score,
  with quality-start streaks and category weighting.
- `compute_clutch_race` — OPS in high-leverage games (close margin or
  top-tier opponent), weighted by clutch AB count.
- `compute_five_tools_race` — fuses player_attributes ratings with
  actual production via percentile ranking; geometric mean rewards
  balanced excellence.
- `compute_undercover_race` — Kindelan formula restricted to batters
  whose computed OVR is below the league average (diamond-in-the-rough).

All four plug into `/mvp-race` as additional tabs.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable

from db import get_db
from lib.scoring import MVP_TEAM_MULTIPLIER
from lib.season import Phase
from lib.stats import BattingLine, PitchingLine
from models import Player, Team

from .services import (
    CategoryBonus,
    RaceEntry,
    _team_context,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _percentile_ranks(values: list[float]) -> list[float]:
    """Return a 0..1 percentile rank for each value (higher value → higher rank).

    Ties share their average rank. Empty input returns empty.
    """
    n = len(values)
    if n == 0:
        return []
    indexed = sorted(enumerate(values), key=lambda p: p[1])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j) / 2  # 0-indexed mean
        for k in range(i, j + 1):
            orig_idx = indexed[k][0]
            ranks[orig_idx] = avg_rank / (n - 1) if n > 1 else 1.0
        i = j + 1
    return ranks


def _build_entry(
    player_row: dict[str, Any],
    key_stat_label: str,
    key_stat_value: float,
    base: float,
    bonuses: list[CategoryBonus],
    rank_by_tid: dict[int, int],
    position: str | None = None,
    apply_team_multiplier: bool = True,
) -> RaceEntry:
    """Shared RaceEntry assembly.

    `apply_team_multiplier`: if False, mult is forced to 1.0 and the team
    standing is ignored. The four individual-achievement awards (Artesano,
    Clutch, Cinco Herramientas, Encubierto) use this — only Kindelan and
    Lazo apply the team mult, since they're season-MVP awards where
    winning context matters.
    """
    tid = player_row["team_id"]
    team_rank = rank_by_tid.get(tid, 8)
    mult = MVP_TEAM_MULTIPLIER.get(team_rank, 1.0) if apply_team_multiplier else 1.0
    bonus_total = sum(b.points for b in bonuses)
    raw = base + bonus_total
    return RaceEntry(
        player_id=player_row["id"],
        player_name=player_row["name"],
        position=position if position is not None else player_row.get("position"),
        team_id=tid,
        team_short=player_row["short_name"],
        team_color=player_row["color_primary"],
        team_logo=player_row["logo_file"],
        team_rank=team_rank,
        key_stat_label=key_stat_label,
        key_stat_value=key_stat_value,
        base=round(base, 2),
        bonuses=bonuses,
        bonus_total=bonus_total,
        multiplier=mult,
        final=round(raw * mult, 2),
    )


# ---------------------------------------------------------------------------
# Premio al Artesano — starter Cy Young by per-start game score
# ---------------------------------------------------------------------------

def _game_score(ip_outs: int, so: int, er: int, bb: int, hr_allowed: int) -> int:
    """Simplified Bill James game score.

    IP_outs + 2*SO − 3*ER − 2*BB − 4*HR_allowed. Higher is better.
    A stock 6-inning, 5 SO, 2 ER, 1 BB, 0 HR start → 18 + 10 − 6 − 2 = 20.
    """
    return ip_outs + 2 * so - 3 * er - 2 * bb - 4 * hr_allowed


def compute_artesano_race() -> list[RaceEntry]:
    """Starting pitcher award. Each start scored individually.

    - Quality Start:  IP_outs >= 18 AND ER <= 3.
    - Dominant Start: IP_outs >= 21 AND ER <= 1.
    - Disaster:       IP_outs <  9  OR  ER >= 6.
    - Base = sum(game_scores) + total_IP_outs + 10×dominant − 15×disaster + 2×longest_QS_streak
    - Bonus: top-5 in QS count, top-5 in DOM count, top-5 in FEWEST disasters.
    - NO team multiplier (individual craft award, not team MVP).
    - Qualification: role='rotation' AND (>= 2 appearances OR >= 15 cumulative outs).
    """
    rank_by_tid, _ = _team_context()

    rows = get_db().execute("""
        SELECT ps.player_id, p.name, p.position, p.team_id,
            t.short_name, t.color_primary, t.logo_file,
            ps.IP_outs, ps.SO, ps.ER, ps.BB, ps.HR_allowed,
            s.game_num
        FROM pitching_stats ps
        JOIN players p ON ps.player_id = p.id
        JOIN teams t ON p.team_id = t.id
        JOIN games g ON ps.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        WHERE p.role = 'rotation' AND s.phase = ?
        ORDER BY ps.player_id, s.game_num
    """, (Phase.REGULAR,)).fetchall()

    # Bucket by player
    by_player: dict[int, list[dict]] = {}
    identity: dict[int, dict[str, Any]] = {}
    for r in rows:
        pid = r["player_id"]
        by_player.setdefault(pid, []).append({
            "IP_outs": r["IP_outs"], "SO": r["SO"], "ER": r["ER"],
            "BB": r["BB"], "HR_allowed": r["HR_allowed"], "game_num": r["game_num"],
        })
        identity.setdefault(pid, {
            "id": pid, "name": r["name"], "position": r["position"],
            "team_id": r["team_id"], "short_name": r["short_name"],
            "color_primary": r["color_primary"], "logo_file": r["logo_file"],
        })

    # First pass: compute per-pitcher stats (for grading + final score)
    from blueprints.mvp_race.services import _grade_ranks
    stats: list[dict[str, Any]] = []
    for pid, starts in by_player.items():
        total_outs = sum(s["IP_outs"] for s in starts)
        if len(starts) < 2 and total_outs < 15:
            continue
        scores = [_game_score(s["IP_outs"], s["SO"], s["ER"],
                              s["BB"], s["HR_allowed"]) for s in starts]
        is_qs = [s["IP_outs"] >= 18 and s["ER"] <= 3 for s in starts]
        qs_count  = sum(1 for q in is_qs if q)
        dominant  = sum(1 for s in starts if s["IP_outs"] >= 21 and s["ER"] <= 1)
        disaster  = sum(1 for s in starts if s["IP_outs"] < 9 or s["ER"] >= 6)
        longest = cur = 0
        for q in is_qs:
            cur = cur + 1 if q else 0
            longest = max(longest, cur)
        stats.append({
            "id": pid,
            "identity": identity[pid],
            "qs": qs_count, "dominant": dominant, "disaster": disaster,
            "total_outs": total_outs,
            "neg_disaster": -disaster,  # so "higher is better" means fewer disasters
            "base_pre_bonus": (
                sum(scores) + total_outs + 10 * dominant - 15 * disaster + 2 * longest
            ),
            "avg_gs": sum(scores) / len(scores),
        })

    if not stats:
        return []

    # Top-5 graded bonuses — tiebreak by IP_outs (workhorses win ties).
    qs_grades  = _grade_ranks(stats, "qs",           tiebreak="total_outs")
    dom_grades = _grade_ranks(stats, "dominant",     tiebreak="total_outs")
    dis_grades = _grade_ranks(stats, "neg_disaster", tiebreak="total_outs")

    results: list[RaceEntry] = []
    for s in stats:
        pid = s["id"]
        qs_b  = qs_grades.get(pid, (None, 0))
        dom_b = dom_grades.get(pid, (None, 0))
        dis_b = dis_grades.get(pid, (None, 0))
        bonuses = [
            CategoryBonus("QS",  qs_b[0],  qs_b[1]),
            CategoryBonus("DOM", dom_b[0], dom_b[1]),
            CategoryBonus("DIS", dis_b[0], dis_b[1]),
        ]
        entry = _build_entry(
            s["identity"],
            key_stat_label="Avg GS",
            key_stat_value=round(s["avg_gs"], 1),
            base=s["base_pre_bonus"],
            bonuses=bonuses,
            rank_by_tid=rank_by_tid,
            apply_team_multiplier=False,
        )
        results.append(entry)

    return sorted(results, key=lambda r: (-r.final, r.player_id))[:25]


# ---------------------------------------------------------------------------
# Premio Clutch — OPS in high-leverage games
# ---------------------------------------------------------------------------

def _top4_by_week() -> dict[int, set[int]]:
    """Return {week_num: set_of_top4_team_ids} from stored power_rankings.

    `weekly_awards.power_rankings` is persisted JSON — the top-4 snapshot
    as-of end of that week. For a game played in week N, the "top 4 at
    the time" is week N-1's snapshot (what teams were ranked top 4 BEFORE
    this game happened). The caller looks up `by_week.get(game_week - 1)`.
    """
    import json
    rows = get_db().execute(
        "SELECT week_num, power_rankings FROM weekly_awards "
        "WHERE power_rankings IS NOT NULL"
    ).fetchall()
    out: dict[int, set[int]] = {}
    for r in rows:
        try:
            ranking = json.loads(r["power_rankings"])
        except (TypeError, ValueError):
            continue
        # Top 4 by rank ascending (rank=1 is best)
        top4 = sorted(ranking, key=lambda e: e.get("rank", 99))[:4]
        out[r["week_num"]] = {e["team_id"] for e in top4 if "team_id" in e}
    return out


def compute_clutch_race() -> list[RaceEntry]:
    """Batter award — performance in high-leverage games.

    A game is "high-leverage" when any of these holds:
      • final margin ≤ 2 runs, OR
      • opponent was top 4 in the **power rankings as of the previous week**
        (time-aware — NOT current standings). Falls back to margin-only for
        week 1 or weeks where no rankings snapshot exists.

    Score = OPS_in_clutch × 100 × sqrt(clutch_AB / 10). No team multiplier.
    The sqrt term prevents a small-sample hero (2-for-3 in one game) from
    topping someone who was consistently good in many clutch spots.
    Qualification: clutch_AB >= 10.
    """
    rank_by_tid, _ = _team_context()
    top4_by_week = _top4_by_week()

    rows = get_db().execute("""
        SELECT bs.player_id, p.name, p.position, p.team_id,
            t.short_name, t.color_primary, t.logo_file,
            bs.AB, bs.R, bs.H, bs.doubles, bs.triples, bs.HR, bs.RBI,
            bs.BB, bs.SO, bs.SB,
            g.home_runs, g.away_runs,
            s.home_team_id, s.away_team_id, s.week_num
        FROM batting_stats bs
        JOIN players p ON bs.player_id = p.id
        JOIN teams t ON p.team_id = t.id
        JOIN games g ON bs.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        WHERE s.phase = ?
    """, (Phase.REGULAR,)).fetchall()

    # Accumulate clutch-only totals per player
    totals: dict[int, dict[str, int]] = {}
    identity: dict[int, dict[str, Any]] = {}
    for r in rows:
        margin = abs((r["home_runs"] or 0) - (r["away_runs"] or 0))
        opponent_id = (
            r["away_team_id"] if r["home_team_id"] == r["team_id"]
            else r["home_team_id"]
        )
        # Use the top-4 snapshot from the previous week — the rankings
        # "in force" when this game was played.
        prev_week_top4 = top4_by_week.get((r["week_num"] or 0) - 1, set())
        is_clutch = margin <= 2 or opponent_id in prev_week_top4
        if not is_clutch:
            continue
        pid = r["player_id"]
        t = totals.setdefault(pid, {k: 0 for k in (
            "AB", "R", "H", "doubles", "triples", "HR", "RBI", "BB", "SO", "SB",
        )})
        for k in t:
            t[k] += r[k] or 0
        identity.setdefault(pid, {
            "id": pid, "name": r["name"], "position": r["position"],
            "team_id": r["team_id"], "short_name": r["short_name"],
            "color_primary": r["color_primary"], "logo_file": r["logo_file"],
        })

    from math import sqrt

    qualified: list[dict[str, Any]] = []
    for pid, t in totals.items():
        if t["AB"] < 10:
            continue
        line = BattingLine(**t)
        qualified.append({
            "id": pid, "identity": identity[pid], "line": line,
            "AB": t["AB"], "H": t["H"], "HR": t["HR"],
            "clutch_OPS": line.OPS,
        })

    if not qualified:
        return []

    # No bonus on this award — base = OPS × 100 × sqrt(AB/10) already fuses
    # quality and volume into the whole statement. Top-5 in clutch H/HR
    # would correlate with OPS and double-count.
    results: list[RaceEntry] = []
    for q in qualified:
        base = q["line"].OPS * 100 * sqrt(q["AB"] / 10)
        entry = _build_entry(
            q["identity"],
            key_stat_label="Clutch OPS",
            key_stat_value=q["line"].OPS,
            base=base,
            bonuses=[],
            rank_by_tid=rank_by_tid,
            apply_team_multiplier=False,
        )
        results.append(entry)

    return sorted(results, key=lambda r: (-r.final, r.player_id))[:25]


# ---------------------------------------------------------------------------
# Premio Cinco Herramientas — scouting × production fusion
# ---------------------------------------------------------------------------

def compute_five_tools_race() -> list[RaceEntry]:
    """Batter award rewarding balance across three tools.

    Each tool combines the scouting attribute and the produced stat:
      Contact tool = 0.4 × pctile(contact_vs_l+vs_r) + 0.6 × pctile(AVG)
      Power tool   = 0.4 × pctile(power_vs_l+vs_r)   + 0.6 × pctile(ISO)
      Speed tool   = 0.4 × pctile(attr_speed)        + 0.6 × pctile(SB_rate)

    Final = 100 × geomean(Contact, Power, Speed) × team_multiplier

    Geomean penalizes one-dimensional players — a 0.9/0.9/0.3 triple-tool
    loses to 0.7/0.7/0.7. Qualification: AB >= 1 × team_games.
    """
    rank_by_tid, games_by_tid = _team_context()

    rows = get_db().execute("""
        SELECT p.id, p.name, p.position, p.team_id,
            t.short_name, t.color_primary, t.logo_file,
            SUM(bs.AB) AS AB, SUM(bs.H) AS H, SUM(bs.doubles) AS doubles,
            SUM(bs.triples) AS triples, SUM(bs.HR) AS HR, SUM(bs.BB) AS BB,
            SUM(bs.SO) AS SO, SUM(bs.RBI) AS RBI, SUM(bs.R) AS R,
            SUM(bs.SB) AS SB,
            pa.contact_vs_l, pa.contact_vs_r,
            pa.power_vs_l, pa.power_vs_r, pa.speed
        FROM batting_stats bs
        JOIN players p ON bs.player_id = p.id
        JOIN teams t ON p.team_id = t.id
        LEFT JOIN player_attributes pa ON pa.player_id = p.id
        WHERE pa.contact_vs_l IS NOT NULL
        GROUP BY p.id
        HAVING SUM(bs.AB) > 0
    """).fetchall()

    qualified: list[dict[str, Any]] = []
    for r in rows:
        tg = games_by_tid.get(r["team_id"], 0)
        if tg == 0 or r["AB"] < tg:  # at least 1 AB per team game
            continue
        line = BattingLine.from_row(r)
        # Speed proxy: runs scored per time on base. Fast runners score
        # from 2nd on singles, take the extra base, tag up on flies.
        # Slow runners who walk a lot and trot home score less often.
        times_on_base = (r["H"] or 0) + (r["BB"] or 0)
        r_per_tob = (r["R"] or 0) / times_on_base if times_on_base else 0.0
        qualified.append({
            **dict(r),
            "_AVG": line.AVG,
            "_ISO": line.ISO,
            "_R_per_TOB": r_per_tob,
            "_contact_attr": (r["contact_vs_l"] or 0) + (r["contact_vs_r"] or 0),
            "_power_attr":   (r["power_vs_l"] or 0) + (r["power_vs_r"] or 0),
            "_speed_attr":   r["speed"] or 0,
        })

    if not qualified:
        return []

    # Percentile ranks across the qualified pool
    pr_avg     = _percentile_ranks([q["_AVG"] for q in qualified])
    pr_iso     = _percentile_ranks([q["_ISO"] for q in qualified])
    pr_rtob    = _percentile_ranks([q["_R_per_TOB"] for q in qualified])
    pr_contact = _percentile_ranks([q["_contact_attr"] for q in qualified])
    pr_power   = _percentile_ranks([q["_power_attr"] for q in qualified])
    pr_speed   = _percentile_ranks([q["_speed_attr"] for q in qualified])

    from math import pow as _pow

    # No bonus — the base already IS a percentile-weighted composite of
    # the three tools. Grading top-5 in the same three tools would be
    # pure double-counting of what the geometric mean already captured.
    results: list[RaceEntry] = []
    for i, q in enumerate(qualified):
        contact = 0.4 * pr_contact[i] + 0.6 * pr_avg[i]
        power   = 0.4 * pr_power[i]   + 0.6 * pr_iso[i]
        speed   = 0.4 * pr_speed[i]   + 0.6 * pr_rtob[i]
        geo = _pow(max(contact, 0.01) * max(power, 0.01) * max(speed, 0.01), 1 / 3)
        entry = _build_entry(
            q, key_stat_label="Balance",
            key_stat_value=round(geo, 3),
            base=geo * 100, bonuses=[], rank_by_tid=rank_by_tid,
            apply_team_multiplier=False,
        )
        results.append(entry)

    return sorted(results, key=lambda r: (-r.final, r.player_id))[:25]


# ---------------------------------------------------------------------------
# Premio Encubierto — below-average OVR batter using Kindelan formula
# ---------------------------------------------------------------------------

def league_avg_overall() -> tuple[float, dict[int, float]]:
    """Public wrapper — routes use this to surface the threshold in the UI."""
    return _league_avg_overall()


def _league_avg_overall() -> tuple[float, dict[int, float]]:
    """Return (league_avg_overall, overall_by_player_id) for batters.

    Batter OVR = mean of (power_vs_l, contact_vs_l, power_vs_r, contact_vs_r, speed).
    """
    rows = get_db().execute("""
        SELECT p.id,
            ROUND((pa.power_vs_l + pa.contact_vs_l + pa.power_vs_r
                 + pa.contact_vs_r + pa.speed) / 5.0, 2) AS overall
        FROM players p
        JOIN player_attributes pa ON pa.player_id = p.id
        WHERE pa.power_vs_l IS NOT NULL
    """).fetchall()
    overalls = {r["id"]: r["overall"] for r in rows if r["overall"] is not None}
    if not overalls:
        return 0.0, {}
    avg = sum(overalls.values()) / len(overalls)
    return avg, overalls


def compute_undercover_race() -> list[RaceEntry]:
    """Best performance by a batter whose OVR is BELOW the league average.

    Uses the Kindelan base formula (OPS × 100) + reduced bonus weight, but
    only players with computed OVR < league_avg qualify. Highlights hidden
    gems who outperform their scouting profile.

    Qualification:
      • batter with player_attributes (for OVR computation)
      • OVR < league-avg OVR
      • AB + BB >= 1 × team_games (looser than Kindelan's 2×)
    """

    rank_by_tid, games_by_tid = _team_context()
    league_avg, overalls = _league_avg_overall()
    if league_avg == 0:
        return []

    rows = get_db().execute("""
        SELECT p.id, p.name, p.position, p.team_id,
            t.short_name, t.color_primary, t.logo_file,
            SUM(bs.AB) AS AB, SUM(bs.R) AS R, SUM(bs.H) AS H,
            SUM(bs.doubles) AS doubles, SUM(bs.triples) AS triples,
            SUM(bs.HR) AS HR, SUM(bs.RBI) AS RBI, SUM(bs.BB) AS BB,
            SUM(bs.SO) AS SO, SUM(bs.SB) AS SB
        FROM batting_stats bs
        JOIN players p ON bs.player_id = p.id
        JOIN teams t ON p.team_id = t.id
        GROUP BY p.id
        HAVING SUM(bs.AB) > 0
    """).fetchall()

    qualified: list[dict[str, Any]] = []
    for r in rows:
        ovr = overalls.get(r["id"])
        if ovr is None or ovr >= league_avg:
            continue
        tg = games_by_tid.get(r["team_id"], 0)
        if tg == 0 or (r["AB"] + r["BB"]) < tg:
            continue
        line = BattingLine.from_row(r)
        qualified.append({
            **dict(r),
            "OPS": line.OPS, "AVG": line.AVG, "_ovr": ovr,
            "_gap": league_avg - ovr,  # how far below average
        })

    # No bonus — the narrative here is "below-average OVR outperforming their
    # scout rating". OPS is the signal, the OVR gap is the tiebreaker-ish
    # term. Triple-crown bonuses among undercovers would mostly just mirror
    # Kindelan's structure without adding new information about the hidden-gem
    # question.
    results: list[RaceEntry] = []
    for q in qualified:
        base = q["OPS"] * 100 + q["_gap"] * 0.5
        entry = _build_entry(
            q, key_stat_label="OPS",
            key_stat_value=q["OPS"],
            base=base, bonuses=[], rank_by_tid=rank_by_tid,
            apply_team_multiplier=False,
        )
        results.append(entry)

    return sorted(results, key=lambda r: (-r.final, r.player_id))[:25]
