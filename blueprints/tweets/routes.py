"""Tweets blueprint routes."""
from __future__ import annotations

from flask import render_template

from blueprints.antesala.services import get_tweets_by_game

from . import tweets_bp


@tweets_bp.route('/tweets')
def tweets() -> str:
    tweets_by_game = get_tweets_by_game()
    return render_template('tweets.html', tweets_by_game=tweets_by_game)
