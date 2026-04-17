"""Main blueprint routes."""
from __future__ import annotations

from flask import render_template

from lib.season import TOTAL_GAMES
from models import Team
from models.game import recent_games

from . import main_bp
from services.standings import get_standings


@main_bp.route('/')
def index() -> str:
    standings = get_standings()
    teams = Team.all()
    games_played = sum(s['wins'] + s['losses'] for s in standings) // 2
    return render_template(
        'index.html',
        standings=standings,
        recent=recent_games(),
        teams=teams,
        games_played=games_played,
        total_games=TOTAL_GAMES,
    )
