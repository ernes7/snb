"""Teams blueprint routes.

Migrated to the domain-model layer — all DB access goes through `Team`.
The old `services.py` helpers are kept temporarily for any external
callers; once every consumer is on models, it can be deleted.
"""
from __future__ import annotations

from flask import abort, render_template

from models import Team

from . import teams_bp


@teams_bp.route('/team/<short>')
def team(short: str) -> str:
    team_obj = Team.get(short)
    if not team_obj:
        abort(404)

    roster = team_obj.roster_by_role()
    return render_template(
        'team.html',
        team=team_obj,
        stats=team_obj.record(),
        lineup=roster["lineup"],
        bench=roster["bench"],
        rotation=roster["rotation"],
        bullpen=roster["bullpen"],
        bat_leaders=team_obj.bat_leaders(),
        pitch_leaders=team_obj.pitch_leaders(),
        bat_totals=team_obj.batting_totals(),
        pitch_totals=team_obj.pitching_totals(),
        team_errors=team_obj.errors_committed(),
    )
