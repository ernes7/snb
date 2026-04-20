"""Tweets blueprint — game-by-game tweet feed."""
from flask import Blueprint

tweets_bp = Blueprint('tweets', __name__)

from . import routes  # noqa: E402
