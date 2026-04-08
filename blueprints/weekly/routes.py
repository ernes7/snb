"""Weekly blueprint routes."""
from __future__ import annotations

from flask import abort, render_template

from . import weekly_bp
from services.weekly import get_weekly_data


@weekly_bp.route('/weekly')
@weekly_bp.route('/weekly/<int:week_num>')
def weekly(week_num: int = 1) -> str:
    data = get_weekly_data(week_num)
    if not data:
        abort(404)
    return render_template('weekly.html', **data)
