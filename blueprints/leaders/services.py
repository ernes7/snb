"""Leaders blueprint services.

Thin filter/sort layer over `services.player_stats`. All rate-stat math
and aggregate queries live in that shared module; this file only picks
top-5 slices by different keys.
"""
from __future__ import annotations

from typing import Any

from services.player_stats import (
    get_all_batting_lines,
    get_all_pitching_lines,
    get_weekly_batting_series,
    get_weekly_pitching_series,
)


def _attach_spark(leaders: list[dict[str, Any]], series: dict[int, list[float]]) -> list[dict[str, Any]]:
    for e in leaders:
        e["spark"] = series.get(e["id"], [])
    return leaders


def get_bat_avg_leaders() -> list[dict[str, Any]]:
    """Top 5 batting average leaders (min 5 AB)."""
    qualified = [e for e in get_all_batting_lines() if e["AB"] >= 5]
    top = sorted(qualified, key=lambda e: e["AVG"], reverse=True)[:5]
    return _attach_spark(top, get_weekly_batting_series("AVG"))


def get_bat_ops_leaders() -> list[dict[str, Any]]:
    """Top 5 OPS leaders (min 5 AB)."""
    qualified = [e for e in get_all_batting_lines() if e["AB"] >= 5]
    top = sorted(qualified, key=lambda e: e["OPS"], reverse=True)[:5]
    return _attach_spark(top, get_weekly_batting_series("OPS"))


def get_bat_hr_leaders() -> list[dict[str, Any]]:
    """Top 5 home run leaders."""
    qualified = [e for e in get_all_batting_lines() if e["HR"] > 0]
    top = sorted(qualified, key=lambda e: e["HR"], reverse=True)[:5]
    return _attach_spark(top, get_weekly_batting_series("OPS"))


def get_bat_hits_leaders() -> list[dict[str, Any]]:
    """Top 5 hits leaders."""
    qualified = [e for e in get_all_batting_lines() if e["H"] > 0]
    top = sorted(qualified, key=lambda e: e["H"], reverse=True)[:5]
    return _attach_spark(top, get_weekly_batting_series("AVG"))


def get_bat_rbi_leaders() -> list[dict[str, Any]]:
    """Top 5 RBI leaders."""
    qualified = [e for e in get_all_batting_lines() if e["RBI"] > 0]
    top = sorted(qualified, key=lambda e: e["RBI"], reverse=True)[:5]
    return _attach_spark(top, get_weekly_batting_series("OPS"))


def get_pitch_wins_leaders() -> list[dict[str, Any]]:
    """Top 5 wins leaders."""
    qualified = [e for e in get_all_pitching_lines() if e["W"] > 0]
    top = sorted(qualified, key=lambda e: e["W"], reverse=True)[:5]
    return _attach_spark(top, get_weekly_pitching_series("ERA"))


def get_pitch_era_leaders() -> list[dict[str, Any]]:
    """Top 5 ERA leaders (min 9 outs / 3 IP)."""
    qualified = [e for e in get_all_pitching_lines() if e["IP_outs"] >= 9]
    top = sorted(qualified, key=lambda e: e["ERA"])[:5]
    return _attach_spark(top, get_weekly_pitching_series("ERA"))


def get_pitch_whip_leaders() -> list[dict[str, Any]]:
    """Top 5 WHIP leaders (min 9 outs / 3 IP)."""
    qualified = [e for e in get_all_pitching_lines() if e["IP_outs"] >= 9]
    top = sorted(qualified, key=lambda e: e["WHIP"])[:5]
    return _attach_spark(top, get_weekly_pitching_series("WHIP"))


def get_pitch_so_leaders() -> list[dict[str, Any]]:
    """Top 5 strikeout leaders."""
    qualified = [e for e in get_all_pitching_lines() if e["SO"] > 0]
    top = sorted(qualified, key=lambda e: e["SO"], reverse=True)[:5]
    return _attach_spark(top, get_weekly_pitching_series("K9"))
