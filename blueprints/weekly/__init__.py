"""Weekly blueprint — weekly recap with POTW, power rankings, and tweets."""
from flask import Blueprint

weekly_bp = Blueprint('weekly', __name__)

from . import routes  # noqa: E402
