"""Team stats blueprint routes."""
from __future__ import annotations

from flask import render_template

from . import team_stats_bp
from .services import get_team_batting_leaders, get_team_pitching_leaders


@team_stats_bp.route('/team-stats')
def team_stats() -> str:
    return render_template('team_stats.html',
                           bat_teams=get_team_batting_leaders(),
                           pitch_teams=get_team_pitching_leaders())
