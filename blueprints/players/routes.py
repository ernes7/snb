"""Players blueprint routes."""
from __future__ import annotations

from flask import abort, render_template

from . import players_bp
from .services import get_player, get_player_attrs, get_player_draft, \
    get_batting_log, get_batting_totals, get_pitching_log, get_pitching_totals


@players_bp.route('/player/<int:player_id>')
def player(player_id: int) -> str:
    p = get_player(player_id)
    if not p:
        abort(404)

    attrs = get_player_attrs(player_id)
    draft = get_player_draft(player_id)
    bat_games = get_batting_log(player_id)
    bat_totals = get_batting_totals(player_id)
    pitch_games = get_pitching_log(player_id)
    pitch_totals = get_pitching_totals(player_id)

    return render_template('player.html', player=p, draft=draft, attrs=attrs,
                           bat_games=bat_games, bat_totals=bat_totals,
                           pitch_games=pitch_games, pitch_totals=pitch_totals)
