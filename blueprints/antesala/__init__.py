"""Antesala blueprint — analyst show with predictions and tweets."""
from flask import Blueprint

antesala_bp = Blueprint('antesala', __name__)

from . import routes  # noqa: E402
