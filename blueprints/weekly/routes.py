"""Weekly blueprint routes."""
from __future__ import annotations

from flask import abort, render_template

from models import Week
from services.weekly import get_weekly_data

from . import weekly_bp


@weekly_bp.route('/weekly')
@weekly_bp.route('/weekly/<int:week_num>')
def weekly(week_num: int | None = None) -> str:
    max_week = Week.latest_with_games()
    if week_num is None:
        week_num = max_week
    data = get_weekly_data(week_num)
    if not data:
        abort(404)
    data["max_week"] = max_week
    return render_template('weekly.html', **data)
