"""Playoffs blueprint — playoff bracket display."""
from flask import Blueprint

playoffs_bp = Blueprint('playoffs', __name__)

from . import routes  # noqa: E402
