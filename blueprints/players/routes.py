"""Players blueprint routes — model-backed."""
from __future__ import annotations

from flask import abort, render_template

from models import Player

from . import players_bp


@players_bp.route('/jugadores')
def all_players() -> str:
    return render_template('all_players.html',
                           players=Player.all_with_attrs_and_overall())


@players_bp.route('/player/<int:player_id>')
def player(player_id: int) -> str:
    p = Player.get_with_team(player_id)
    if not p:
        abort(404)

    bat_games = p.batting_log()
    pitch_games = p.pitching_log()
    return render_template(
        'player.html',
        player=p,
        draft=p.draft_info(),
        attrs=p.attributes(),
        bat_games=bat_games,
        bat_totals=p.batting_line(),
        pitch_games=pitch_games,
        pitch_totals=p.pitching_line(),
        bat_spark=p.batting_sparkline(),
        pitch_spark=p.pitching_sparkline(),
    )
