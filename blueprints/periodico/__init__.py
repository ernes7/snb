"""En Tres y Dos — Serie Nacional newspaper blueprint."""
from flask import Blueprint

periodico_bp = Blueprint('periodico', __name__)

from . import routes  # noqa: E402, F401
