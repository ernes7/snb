"""Schedule blueprint routes."""
from __future__ import annotations

from itertools import groupby

from flask import render_template

from . import schedule_bp
from .services import (
    get_schedule_games, get_unavailable_pitchers,
    get_game_picks_for_schedule, get_games_of_week,
    get_probable_starters,
)


@schedule_bp.route('/schedule')
def schedule() -> str:
    games = get_schedule_games()
    played = sum(1 for g in games if g['home_runs'] is not None)
    weeks = [(wk, list(wg)) for wk, wg in groupby(games, key=lambda g: g['week_num'])]
    # Current week = first week with any unplayed game
    current_week = next(
        (wk for wk, wg in weeks if any(g['home_runs'] is None for g in wg)),
        None,
    )
    unavailable = get_unavailable_pitchers()
    picks = get_game_picks_for_schedule()
    games_of_week = get_games_of_week()
    starters = get_probable_starters()
    return render_template('schedule.html', weeks=weeks, played=played,
                           unavailable=unavailable, picks=picks,
                           games_of_week=games_of_week, starters=starters,
                           current_week=current_week)
