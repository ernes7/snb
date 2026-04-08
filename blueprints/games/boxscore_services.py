"""Games blueprint box score services."""
from __future__ import annotations

from typing import Any

from werkzeug.datastructures import ImmutableMultiDict

from db import get_db


def get_boxscore_form_data(game_id: int) -> dict[str, Any] | None:
    """Get all data needed for the box score entry form."""
    db = get_db()

    game = db.execute("""
        SELECT g.*, s.game_num, s.home_team_id, s.away_team_id,
            ht.name as home_name, ht.short_name as home_short, ht.color_primary as home_color,
            at.name as away_name, at.short_name as away_short, at.color_primary as away_color
        FROM games g
        JOIN schedule s ON g.schedule_id = s.id
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        WHERE g.id = ?
    """, (game_id,)).fetchone()

    if not game:
        return None

    home_batters = db.execute("""
        SELECT * FROM players WHERE team_id=? AND role IN ('lineup','bench')
        ORDER BY CASE role WHEN 'lineup' THEN 0 ELSE 1 END, lineup_order
    """, (game['home_team_id'],)).fetchall()

    away_batters = db.execute("""
        SELECT * FROM players WHERE team_id=? AND role IN ('lineup','bench')
        ORDER BY CASE role WHEN 'lineup' THEN 0 ELSE 1 END, lineup_order
    """, (game['away_team_id'],)).fetchall()

    home_pitchers = db.execute("""
        SELECT * FROM players WHERE team_id=? AND role IN ('rotation','bullpen')
        ORDER BY CASE role WHEN 'rotation' THEN 0 ELSE 1 END, lineup_order
    """, (game['home_team_id'],)).fetchall()

    away_pitchers = db.execute("""
        SELECT * FROM players WHERE team_id=? AND role IN ('rotation','bullpen')
        ORDER BY CASE role WHEN 'rotation' THEN 0 ELSE 1 END, lineup_order
    """, (game['away_team_id'],)).fetchall()

    # Load existing stats if editing
    existing_bat = {}
    for row in db.execute("SELECT * FROM batting_stats WHERE game_id=?", (game_id,)).fetchall():
        existing_bat[row['player_id']] = dict(row)

    existing_pit = {}
    for row in db.execute("SELECT * FROM pitching_stats WHERE game_id=?", (game_id,)).fetchall():
        existing_pit[row['player_id']] = dict(row)

    return {
        'game': game,
        'home_batters': home_batters,
        'away_batters': away_batters,
        'home_pitchers': home_pitchers,
        'away_pitchers': away_pitchers,
        'existing_bat': existing_bat,
        'existing_pit': existing_pit,
    }


def save_boxscore(game_id: int, form: ImmutableMultiDict[str, str]) -> None:
    """Save batting and pitching stats from box score form."""
    db = get_db()

    # Get team IDs for this game
    game = db.execute("""
        SELECT s.home_team_id, s.away_team_id
        FROM games g JOIN schedule s ON g.schedule_id = s.id
        WHERE g.id = ?
    """, (game_id,)).fetchone()

    if not game:
        return

    # Delete existing stats for this game (replace approach)
    db.execute("DELETE FROM batting_stats WHERE game_id=?", (game_id,))
    db.execute("DELETE FROM pitching_stats WHERE game_id=?", (game_id,))

    bat_fields = ['AB', 'R', 'H', 'doubles', 'triples', 'HR', 'RBI', 'BB', 'SO', 'SB']
    pit_fields = ['IP_outs', 'H', 'R', 'ER', 'BB', 'SO', 'HR_allowed', 'pitches']

    # Process batting stats
    for key in form:
        if not key.startswith('bat__'):
            continue
        parts = key.split('__')
        if len(parts) != 3:
            continue
        _, pid_str, field = parts
        if field != bat_fields[0]:
            continue  # Only process once per player (triggered by AB)

        player_id = int(pid_str)
        # Determine team
        player = db.execute("SELECT team_id FROM players WHERE id=?", (player_id,)).fetchone()
        if not player:
            continue
        team_id = player['team_id']

        vals = []
        has_data = False
        for f in bat_fields:
            v = int(form.get(f'bat__{player_id}__{f}', '0') or '0')
            vals.append(v)
            if v > 0:
                has_data = True

        if has_data:
            db.execute("""
                INSERT INTO batting_stats (game_id, player_id, team_id, AB, R, H, doubles, triples, HR, RBI, BB, SO, SB)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (game_id, player_id, team_id, *vals))

    # Process pitching stats
    for key in form:
        if not key.startswith('pit__'):
            continue
        parts = key.split('__')
        if len(parts) != 3:
            continue
        _, pid_str, field = parts
        if field != pit_fields[0]:
            continue  # Only process once per player (triggered by IP_outs)

        player_id = int(pid_str)
        player = db.execute("SELECT team_id FROM players WHERE id=?", (player_id,)).fetchone()
        if not player:
            continue
        team_id = player['team_id']

        vals = []
        has_data = False
        for f in pit_fields:
            v = int(form.get(f'pit__{player_id}__{f}', '0') or '0')
            vals.append(v)
            if v > 0:
                has_data = True

        w = 1 if form.get(f'pit__{player_id}__W') else 0
        l = 1 if form.get(f'pit__{player_id}__L') else 0
        sv = 1 if form.get(f'pit__{player_id}__SV') else 0
        if w or l or sv:
            has_data = True

        if has_data:
            db.execute("""
                INSERT INTO pitching_stats (game_id, player_id, team_id, IP_outs, H, R, ER, BB, SO, HR_allowed, pitches, W, L, SV)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (game_id, player_id, team_id, *vals, w, l, sv))

    db.commit()
