"""Draft blueprint — draft picks display."""
from flask import Blueprint

draft_bp = Blueprint('draft', __name__)

from . import routes  # noqa: E402
