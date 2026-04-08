"""Antesala blueprint routes."""
from __future__ import annotations

from flask import render_template

from . import antesala_bp
from .services import get_analysts, get_predictions_by_analyst, get_tweets_by_game


@antesala_bp.route('/antesala')
def antesala() -> str:
    return render_template('antesala.html',
                           analysts=get_analysts(),
                           preds_by_analyst=get_predictions_by_analyst(),
                           tweets_by_game=get_tweets_by_game())
