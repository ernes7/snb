"""Teams blueprint routes."""
from __future__ import annotations

from flask import abort, render_template

from . import teams_bp
from .services import (get_team, get_roster, get_team_bat_leaders,
                       get_team_pitch_leaders, get_team_batting_totals,
                       get_team_pitching_totals, get_team_errors)
from services.standings import get_standings


@teams_bp.route('/team/<short>')
def team(short: str) -> str:
    t = get_team(short.upper())
    if not t:
        abort(404)

    lineup, bench, rotation, bullpen = get_roster(t['id'])
    standings = get_standings()
    team_stats = next((s for s in standings if s['id'] == t['id']), None)
    bat_leaders = get_team_bat_leaders(t['id'])
    pitch_leaders = get_team_pitch_leaders(t['id'])
    bat_totals = get_team_batting_totals(t['id'])
    pitch_totals = get_team_pitching_totals(t['id'])
    team_errors = get_team_errors(t['id'])

    return render_template('team.html', team=t, lineup=lineup, bench=bench,
                           rotation=rotation, bullpen=bullpen, stats=team_stats,
                           bat_leaders=bat_leaders, pitch_leaders=pitch_leaders,
                           bat_totals=bat_totals, pitch_totals=pitch_totals,
                           team_errors=team_errors)
