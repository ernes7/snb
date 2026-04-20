"""Versus blueprint routes."""
from __future__ import annotations

from flask import abort, render_template

from models.team import Team

from . import versus_bp
from .services import build_matchup_page, build_versus_page


@versus_bp.route('/versus')
def versus() -> str:
    data = build_versus_page()
    return render_template('versus.html', **data)


@versus_bp.route('/versus/<team1>/<team2>')
def matchup(team1: str, team2: str) -> str:
    a = Team.get(team1)
    b = Team.get(team2)
    if not a or not b:
        abort(404)
    if a.id == b.id or a.owner == b.owner:
        abort(404)
    data = build_matchup_page(a, b)
    return render_template('versus_matchup.html', **data)
