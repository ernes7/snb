"""Antesala blueprint routes."""
from __future__ import annotations

from flask import render_template

from services.analyst_stats import (
    get_pick_accuracy_by_team,
    get_pick_streaks,
    get_weekly_accuracy,
)
from services.weekly import get_prediction_records

from . import antesala_bp
from .services import get_analysts, get_predictions_by_analyst


@antesala_bp.route('/antesala')
def antesala() -> str:
    analysts = get_analysts()
    records = get_prediction_records()
    records_by_id = {r['analyst_id']: r for r in records}

    analyst_details: dict[int, dict] = {}
    for a in analysts:
        aid = a['id']
        analyst_details[aid] = {
            'record': records_by_id.get(aid, {}),
            'by_team': get_pick_accuracy_by_team(aid),
            'streaks': get_pick_streaks(aid),
            'weekly': get_weekly_accuracy(aid),
        }

    return render_template('antesala.html',
                           analysts=analysts,
                           preds_by_analyst=get_predictions_by_analyst(),
                           analyst_details=analyst_details)
