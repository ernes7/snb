"""Leaders blueprint routes."""
from __future__ import annotations

from flask import render_template

from . import leaders_bp
from .services import (get_bat_avg_leaders, get_bat_hr_leaders,
                       get_bat_hits_leaders, get_bat_rbi_leaders,
                       get_pitch_wins_leaders, get_pitch_era_leaders,
                       get_pitch_so_leaders)


@leaders_bp.route('/leaders')
def leaders() -> str:
    return render_template('leaders.html',
                           bat_avg=get_bat_avg_leaders(),
                           bat_hr=get_bat_hr_leaders(),
                           bat_hits=get_bat_hits_leaders(),
                           bat_rbi=get_bat_rbi_leaders(),
                           pitch_wins=get_pitch_wins_leaders(),
                           pitch_era=get_pitch_era_leaders(),
                           pitch_so=get_pitch_so_leaders())
