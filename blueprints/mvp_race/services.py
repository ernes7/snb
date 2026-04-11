"""MVP race scoring — Premio Kindelan (batter) + Premio Lazo (pitcher).

Formula (per award):
    raw_score   = base_score + triple_crown_bonus
    final_score = raw_score * team_multiplier

Premio Kindelan (batters):
    base = OPS * 100
    bonus = graded 5/4/3/2/1 points across top-5 in AVG, HR, RBI (max +15)
    qualification: (AB + BB) >= 2.0 * team_games_played

Premio Lazo (pitchers):
    base = max(0, 10 - ERA) * 10
    bonus = graded 5/4/3/2/1 points across top-5 in SO, ERA, IP (max +15)
    qualification: IP_outs >= 2.4 * team_games_played

Team multiplier by standings rank (1=best, 8=worst):
    1.10 / 1.05 / 1.00 / 0.95 / 0.90 / 0.85 / 0.80 / 0.75

Design intent: OPS/ERA is king. The base spread (0-100) dwarfs the max
+/- 15 triple-crown bonus, so a player outside the OPS top 5 cannot win
purely on triple-crown sweeps. The team multiplier applies last, so a
dominant player on a last-place team can still win if their raw score
is ~33% higher than the runner-up's.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.player_stats import get_all_batting_lines, get_all_pitching_lines
from services.standings import get_standings

TEAM_MULTIPLIER: dict[int, float] = {
    1: 1.10, 2: 1.05, 3: 1.00, 4: 0.95,
    5: 0.90, 6: 0.85, 7: 0.80, 8: 0.75,
}

GRADED_POINTS = [5, 4, 3, 2, 1]  # Points for ranks 1..5


@dataclass(frozen=True)
class CategoryBonus:
    """Bonus points earned in a single triple-crown category."""
    label: str          # e.g. "AVG", "HR", "RBI", "SO", "ERA", "IP"
    rank: int | None    # 1..5 if in top-5, else None
    points: int         # 0 if not in top-5


@dataclass(frozen=True)
class RaceEntry:
    """One row in either MVP race leaderboard."""
    player_id: int
    player_name: str
    position: str | None
    team_id: int
    team_short: str
    team_color: str
    team_logo: str
    team_rank: int
    # Key stat shown in its own column (OPS for Kindelan, ERA for Lazo)
    key_stat_label: str
    key_stat_value: float
    # Score components
    base: float
    bonuses: list[CategoryBonus]  # 3 entries, one per triple-crown category
    bonus_total: int
    multiplier: float
    final: float


def _team_context() -> tuple[dict[int, int], dict[int, int]]:
    """Return (rank_by_team_id, games_played_by_team_id).

    Rank is 1-indexed (1 = first place). Games played is wins + losses.
    """
    standings = get_standings()
    rank_by_tid: dict[int, int] = {}
    games_by_tid: dict[int, int] = {}
    for idx, s in enumerate(standings, start=1):
        rank_by_tid[s["id"]] = idx
        games_by_tid[s["id"]] = s["wins"] + s["losses"]
    return rank_by_tid, games_by_tid


def _grade_ranks(entries: list[dict[str, Any]], key: str,
                 reverse: bool = True) -> dict[int, tuple[int, int]]:
    """Rank entries by `key`; return {entry_id: (rank, points)} for top 5.

    Stable sort with a deterministic tiebreaker on player id. Entries
    outside the top 5 are absent from the return dict.
    """
    ordered = sorted(entries, key=lambda e: (e[key], -e["id"] if reverse else e["id"]),
                     reverse=reverse)
    out: dict[int, tuple[int, int]] = {}
    for idx, e in enumerate(ordered[:5]):
        rank = idx + 1
        out[e["id"]] = (rank, GRADED_POINTS[idx])
    return out


def compute_kindelan_race() -> list[RaceEntry]:
    """Premio Kindelan — batter MVP race."""
    rank_by_tid, games_by_tid = _team_context()
    all_batters = get_all_batting_lines()

    qualified: list[dict[str, Any]] = []
    for e in all_batters:
        team_games = games_by_tid.get(e["team_id"], 0)
        if team_games == 0:
            continue
        if (e["AB"] + e["BB"]) >= 2.0 * team_games:
            qualified.append(e)

    avg_grades = _grade_ranks(qualified, "AVG")
    hr_grades = _grade_ranks(qualified, "HR")
    rbi_grades = _grade_ranks(qualified, "RBI")

    results: list[RaceEntry] = []
    for e in qualified:
        pid = e["id"]
        avg_b = avg_grades.get(pid, (None, 0))
        hr_b = hr_grades.get(pid, (None, 0))
        rbi_b = rbi_grades.get(pid, (None, 0))
        bonuses = [
            CategoryBonus("AVG", avg_b[0], avg_b[1]),
            CategoryBonus("HR", hr_b[0], hr_b[1]),
            CategoryBonus("RBI", rbi_b[0], rbi_b[1]),
        ]
        bonus_total = sum(b.points for b in bonuses)
        base = round(e["OPS"] * 100, 2)
        raw = base + bonus_total
        team_rank = rank_by_tid.get(e["team_id"], 8)
        mult = TEAM_MULTIPLIER.get(team_rank, 1.0)
        final = round(raw * mult, 2)
        results.append(RaceEntry(
            player_id=pid, player_name=e["name"], position=e["position"],
            team_id=e["team_id"], team_short=e["short_name"],
            team_color=e["color_primary"], team_logo=e["logo_file"],
            team_rank=team_rank,
            key_stat_label="OPS", key_stat_value=e["OPS"],
            base=base, bonuses=bonuses, bonus_total=bonus_total,
            multiplier=mult, final=final,
        ))

    return sorted(results, key=lambda r: (-r.final, r.player_id))[:25]


def compute_lazo_race() -> list[RaceEntry]:
    """Premio Lazo — pitcher Cy Young race."""
    rank_by_tid, games_by_tid = _team_context()
    all_pitchers = get_all_pitching_lines()

    qualified: list[dict[str, Any]] = []
    for e in all_pitchers:
        team_games = games_by_tid.get(e["team_id"], 0)
        if team_games == 0:
            continue
        if e["IP_outs"] >= 2.4 * team_games:
            qualified.append(e)

    so_grades = _grade_ranks(qualified, "SO", reverse=True)
    era_grades = _grade_ranks(qualified, "ERA", reverse=False)
    ip_grades = _grade_ranks(qualified, "IP_outs", reverse=True)

    results: list[RaceEntry] = []
    for e in qualified:
        pid = e["id"]
        so_b = so_grades.get(pid, (None, 0))
        era_b = era_grades.get(pid, (None, 0))
        ip_b = ip_grades.get(pid, (None, 0))
        bonuses = [
            CategoryBonus("SO", so_b[0], so_b[1]),
            CategoryBonus("ERA", era_b[0], era_b[1]),
            CategoryBonus("IP", ip_b[0], ip_b[1]),
        ]
        bonus_total = sum(b.points for b in bonuses)
        base = round(max(0.0, 10 - e["ERA"]) * 10, 2)
        raw = base + bonus_total
        team_rank = rank_by_tid.get(e["team_id"], 8)
        mult = TEAM_MULTIPLIER.get(team_rank, 1.0)
        final = round(raw * mult, 2)
        results.append(RaceEntry(
            player_id=pid, player_name=e["name"], position=None,
            team_id=e["team_id"], team_short=e["short_name"],
            team_color=e["color_primary"], team_logo=e["logo_file"],
            team_rank=team_rank,
            key_stat_label="ERA", key_stat_value=e["ERA"],
            base=base, bonuses=bonuses, bonus_total=bonus_total,
            multiplier=mult, final=final,
        ))

    return sorted(results, key=lambda r: (-r.final, r.player_id))[:25]
