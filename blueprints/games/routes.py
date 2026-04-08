"""Games blueprint routes."""
from __future__ import annotations

from flask import abort, redirect, render_template, request, url_for

from . import games_bp
from .services import get_game_detail, get_game_form_data, save_game
from .boxscore_services import get_boxscore_form_data, save_boxscore


@games_bp.route('/game/<int:game_id>')
def game_detail(game_id: int) -> str:
    data = get_game_detail(game_id)
    if not data:
        abort(404)
    return render_template('game_detail.html', **data)


@games_bp.route('/game/new/<int:schedule_id>')
def game_new(schedule_id: int) -> str:
    data = get_game_form_data(schedule_id)
    if not data:
        abort(404)
    return render_template('game_form.html', **data)


@games_bp.route('/game/save', methods=['POST'])
def game_save() -> str:
    game_id = save_game(request.form)
    return redirect(url_for('games.boxscore', game_id=game_id))


@games_bp.route('/game/<int:game_id>/boxscore')
def boxscore(game_id: int) -> str:
    data = get_boxscore_form_data(game_id)
    if not data:
        abort(404)
    return render_template('boxscore_form.html', **data)


@games_bp.route('/game/<int:game_id>/boxscore/save', methods=['POST'])
def boxscore_save(game_id: int) -> str:
    save_boxscore(game_id, request.form)
    return redirect(url_for('schedule.schedule'))
