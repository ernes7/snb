"""MVP race blueprint — Premio Kindelan (batter) + Premio Lazo (pitcher)."""
from flask import Blueprint

mvp_race_bp = Blueprint('mvp_race', __name__)

from . import routes  # noqa: E402
