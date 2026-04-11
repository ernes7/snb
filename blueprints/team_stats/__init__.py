"""Team stats blueprint — team-level batting and pitching leaders."""
from flask import Blueprint

team_stats_bp = Blueprint('team_stats', __name__)

from . import routes  # noqa: E402
