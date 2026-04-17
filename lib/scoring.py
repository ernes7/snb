"""Tournament scoring constants.

Single source of truth for business rules that drive MVP races, analyst
predictions, and power rankings. Changing a weight or threshold here
propagates everywhere. Keep this file narrow — only constants + tiny
helpers, no DB access.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# MVP races — Premio Kindelan (batter) + Premio Lazo (pitcher)
# ---------------------------------------------------------------------------

# Team-rank multiplier applied to raw MVP score (1 = best standings).
MVP_TEAM_MULTIPLIER: dict[int, float] = {
    1: 1.06, 2: 1.04, 3: 1.02, 4: 1.00,
    5: 0.98, 6: 0.96, 7: 0.94, 8: 0.92,
}

# Qualification thresholds, expressed per team-game-played.
KINDELAN_MIN_PA_PER_GAME = 2.0   # (AB + BB) >= 2.0 * team_games
LAZO_MIN_IP_OUTS_PER_GAME = 2.4  # IP_outs >= 2.4 * team_games

# Triple-crown grading: points awarded for ranks 1..5 in each category.
MVP_GRADED_POINTS: list[int] = [5, 4, 3, 2, 1]

# How many rows to return in the MVP race leaderboards.
MVP_RACE_DISPLAY_LIMIT = 25


# ---------------------------------------------------------------------------
# Analyst predictions (services/weekly.py :: generate_game_picks)
# ---------------------------------------------------------------------------

# Per-analyst factor weights. Sum need not equal 1.0 — we compare
# home_score vs away_score, not an absolute scale.
#   fav   — favorite/hate bias
#   rank  — power-ranking edge
#   pitch — best available starter OVR
#   h2h   — head-to-head record
ANALYST_WEIGHTS: dict[int, dict[str, float]] = {
    1: {"fav": 0.40, "rank": 0.20, "pitch": 0.25, "h2h": 0.15},  # Panfilo
    2: {"fav": 0.45, "rank": 0.25, "pitch": 0.15, "h2h": 0.15},  # Chequera
    3: {"fav": 0.35, "rank": 0.25, "pitch": 0.25, "h2h": 0.15},  # Facundo
}

# When the analyst's hate team is playing (but not their fav), the
# non-hate side gets HATE_BIAS_BOOST and the hate side HATE_BIAS_PENALTY.
HATE_BIAS_BOOST = 0.85
HATE_BIAS_PENALTY = 0.15

# Game-of-the-Week scoring: score = quality * QUALITY_WEIGHT + closeness.
GOTW_QUALITY_WEIGHT = 3


# ---------------------------------------------------------------------------
# Power rankings (services/power_rankings.py)
# ---------------------------------------------------------------------------

POWER_RANKING_WEIGHTS: dict[str, float] = {
    "win_pct": 0.10,
    "recent": 0.19,
    "run_diff": 0.14,
    "batting": 0.19,
    "pitching": 0.19,
    "sos": 0.19,
}

# Window size (in weeks) for the "recent form" component, inclusive of
# the current week. week_start = max(1, week_num - (LOOKBACK - 1)).
RECENT_FORM_LOOKBACK_WEEKS = 5
