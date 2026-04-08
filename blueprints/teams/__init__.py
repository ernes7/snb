"""Teams blueprint — team detail pages."""
from flask import Blueprint

teams_bp = Blueprint('teams', __name__)

from . import routes  # noqa: E402
