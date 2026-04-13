"""En Tres y Dos newspaper routes."""
from __future__ import annotations

from flask import abort, render_template

from . import periodico_bp
from .services import get_all_editions, get_edition

from db import get_db


@periodico_bp.route('/periodico')
def periodico_index() -> str:
    editions = get_all_editions()
    return render_template('periodico_index.html', editions=editions)


@periodico_bp.route('/periodico/<int:edition_num>')
def periodico_edition(edition_num: int) -> str:
    edition = get_edition(edition_num)
    if not edition:
        abort(404)
    db = get_db()
    interview = edition["interview"]
    analyst = None
    player = None
    if interview.get("analyst_id"):
        analyst = db.execute(
            "SELECT * FROM analysts WHERE id=?",
            (interview["analyst_id"],),
        ).fetchone()
    if interview.get("player_id"):
        player = db.execute("""
            SELECT p.*, t.short_name, t.logo_file, t.color_primary
            FROM players p JOIN teams t ON p.team_id=t.id
            WHERE p.id=?
        """, (interview["player_id"],)).fetchone()
    return render_template(
        'periodico.html', edition=edition,
        analyst=analyst, player=player,
    )
