"""Playoffs blueprint routes."""
from __future__ import annotations

from flask import render_template

from . import playoffs_bp
from .services import get_series
from services.standings import get_standings


@playoffs_bp.route('/playoffs')
def playoffs() -> str:
    return render_template('playoffs.html',
                           semi_a=get_series('semi_a'),
                           semi_b=get_series('semi_b'),
                           final=get_series('final'),
                           standings=get_standings())
