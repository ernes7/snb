"""Weekly blueprint routes."""
from __future__ import annotations

from flask import abort, render_template

from db import get_db
from . import weekly_bp
from services.weekly import get_weekly_data


@weekly_bp.route('/weekly')
@weekly_bp.route('/weekly/<int:week_num>')
def weekly(week_num: int | None = None) -> str:
    db = get_db()
    max_week = db.execute(
        "SELECT MAX(s.week_num) FROM schedule s "
        "JOIN games g ON g.schedule_id = s.id "
        "WHERE s.phase = 'regular'"
    ).fetchone()[0] or 1
    if week_num is None:
        week_num = max_week
    data = get_weekly_data(week_num)
    if not data:
        abort(404)
    data["max_week"] = max_week
    return render_template('weekly.html', **data)
