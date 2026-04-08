"""Players blueprint — player detail pages."""
from flask import Blueprint

players_bp = Blueprint('players', __name__)

from . import routes  # noqa: E402
