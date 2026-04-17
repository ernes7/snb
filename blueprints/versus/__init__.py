"""Versus blueprint — head-to-head matrix across all teams."""
from flask import Blueprint

versus_bp = Blueprint('versus', __name__)

from . import routes  # noqa: E402
