"""Main blueprint routes."""
from __future__ import annotations

from flask import render_template

from . import main_bp
from .services import get_recent_games
from services.standings import get_standings, get_all_teams


@main_bp.route('/')
def index() -> str:
    standings = get_standings()
    recent = get_recent_games()
    teams = get_all_teams()
    return render_template('index.html', standings=standings, recent=recent, teams=teams)
