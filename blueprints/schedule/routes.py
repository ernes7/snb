"""Schedule blueprint routes."""
from __future__ import annotations

from itertools import groupby

from flask import render_template

from . import schedule_bp
from .services import get_schedule_games, get_unavailable_pitchers


@schedule_bp.route('/schedule')
def schedule() -> str:
    games = get_schedule_games()
    played = sum(1 for g in games if g['home_runs'] is not None)
    weeks = [(wk, list(wg)) for wk, wg in groupby(games, key=lambda g: g['week_num'])]
    unavailable = get_unavailable_pitchers()
    return render_template('schedule.html', weeks=weeks, played=played,
                           unavailable=unavailable)
