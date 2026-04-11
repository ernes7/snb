"""MVP race blueprint routes."""
from __future__ import annotations

from flask import render_template

from . import mvp_race_bp
from .services import compute_kindelan_race, compute_lazo_race


@mvp_race_bp.route('/mvp-race')
def mvp_race() -> str:
    return render_template('mvp_race.html',
                           kindelan=compute_kindelan_race(),
                           lazo=compute_lazo_race())
