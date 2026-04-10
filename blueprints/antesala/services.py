"""Antesala blueprint services."""
from __future__ import annotations

import sqlite3
from typing import Any

from db import get_db


def get_analysts() -> list[sqlite3.Row]:
    """Get all analysts with their favorite and hated team info."""
    return get_db().execute("""
        SELECT a.*, a.avatar_file, ft.name as fav_name, ft.short_name as fav_short,
            ft.color_primary as fav_color, ft.logo_file as fav_logo,
            ht.name as hate_name, ht.short_name as hate_short
        FROM analysts a
        JOIN teams ft ON a.equipo_favorito_id = ft.id
        JOIN teams ht ON a.equipo_odia_id = ht.id
        ORDER BY a.id
    """).fetchall()


def get_predictions_by_analyst() -> dict[str, list[sqlite3.Row]]:
    """Get predictions grouped by analyst handle."""
    predictions = get_db().execute("""
        SELECT ap.*, a.handle, a.emoji
        FROM analyst_predictions ap
        JOIN analysts a ON ap.analyst_id = a.id
        ORDER BY a.id, ap.pred_num
    """).fetchall()

    grouped: dict[str, list[sqlite3.Row]] = {}
    for p in predictions:
        handle = p['handle']
        if handle not in grouped:
            grouped[handle] = []
        grouped[handle].append(p)
    return grouped


def get_tweets_by_game() -> dict[int, dict[str, Any]]:
    """Get tweets grouped by game number, with replies."""
    db = get_db()
    tweets = db.execute("""
        SELECT at.*, a.handle, a.emoji, a.avatar_file,
            g.home_runs, g.away_runs,
            s.game_num,
            ht.name as home_name, ht.short_name as home_short,
            awt.name as away_name, awt.short_name as away_short
        FROM analyst_tweets at
        JOIN analysts a ON at.analyst_id = a.id
        JOIN games g ON at.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams awt ON s.away_team_id = awt.id
        ORDER BY s.game_num, a.id
    """).fetchall()

    # Fetch all replies
    replies = db.execute("""
        SELECT tr.*, c.handle, c.emoji
        FROM tweet_replies tr
        JOIN tweet_commenters c ON tr.commenter_id = c.id
        ORDER BY tr.id
    """).fetchall()
    replies_by_tweet: dict[int, list[dict[str, Any]]] = {}
    for r in replies:
        replies_by_tweet.setdefault(r["tweet_id"], []).append(dict(r))

    grouped: dict[int, dict[str, Any]] = {}
    for t in tweets:
        gnum = t['game_num']
        if gnum not in grouped:
            grouped[gnum] = {'game': t, 'tweets': []}
        tweet_dict = dict(t)
        tweet_dict['replies'] = replies_by_tweet.get(t['id'], [])
        grouped[gnum]['tweets'].append(tweet_dict)
    return grouped
