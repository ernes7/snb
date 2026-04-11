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
    games_played = sum(s['wins'] + s['losses'] for s in standings) // 2
    total_games = 96
    return render_template(
        'index.html', standings=standings, recent=recent, teams=teams,
        games_played=games_played, total_games=total_games,
    )
