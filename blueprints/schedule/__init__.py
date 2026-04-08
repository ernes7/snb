"""Schedule blueprint — regular season schedule."""
from flask import Blueprint

schedule_bp = Blueprint('schedule', __name__)

from . import routes  # noqa: E402
