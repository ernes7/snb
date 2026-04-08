"""Draft blueprint routes."""
from __future__ import annotations

from flask import render_template

from . import draft_bp
from .services import get_draft_picks, get_draft_teams


@draft_bp.route('/draft')
def draft() -> str:
    picks = get_draft_picks()
    teams = get_draft_teams()
    return render_template('draft.html', picks=picks, teams=teams)
