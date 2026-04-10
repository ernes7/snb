"""Player attributes import service — upsert attributes from roster screenshots."""
from __future__ import annotations

from typing import Any

from db import get_db


def upsert_attributes(player_id: int, attrs: dict[str, Any]) -> None:
    """Insert or update player_attributes for a given player.

    Args:
        player_id: The player's ID.
        attrs: Dict with any of: power_vs_l, contact_vs_l, power_vs_r,
               contact_vs_r, speed, stamina, fastball, slider, curveball,
               sinker, changeup, splitter, screwball.
    """
    db = get_db()
    existing = db.execute(
        "SELECT id FROM player_attributes WHERE player_id = ?", (player_id,)
    ).fetchone()

    cols = [
        "power_vs_l", "contact_vs_l", "power_vs_r", "contact_vs_r",
        "speed", "stamina", "fastball", "slider", "curveball",
        "sinker", "changeup", "splitter", "screwball",
        "cutter", "curveball_dirt",
    ]

    if existing:
        sets = ", ".join(f"{c} = ?" for c in cols)
        vals = [attrs.get(c) for c in cols]
        vals.append(existing[0])
        db.execute(f"UPDATE player_attributes SET {sets} WHERE id = ?", vals)
    else:
        db.execute(
            "INSERT INTO player_attributes"
            " (player_id, power_vs_l, contact_vs_l, power_vs_r, contact_vs_r,"
            "  speed, stamina, fastball, slider, curveball, sinker,"
            "  changeup, splitter, screwball, cutter, curveball_dirt)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (player_id, *[attrs.get(c) for c in cols]),
        )


def bulk_upsert(team_short: str, entries: list[dict[str, Any]]) -> int:
    """Upsert attributes for multiple players on a team.

    Args:
        team_short: Team short name (e.g. 'SSP').
        entries: List of dicts, each with 'name' key + attribute keys.

    Returns:
        Number of players processed.
    """
    db = get_db()
    team = db.execute(
        "SELECT id FROM teams WHERE short_name = ?", (team_short,)
    ).fetchone()
    if not team:
        raise ValueError(f"Team not found: {team_short}")

    count = 0
    for entry in entries:
        name = entry["name"]
        player = db.execute(
            "SELECT id FROM players WHERE name = ? AND team_id = ?",
            (name, team[0]),
        ).fetchone()
        if not player:
            print(f"  WARNING: Player not found: {name} ({team_short})")
            continue

        attrs = {k: v for k, v in entry.items() if k != "name"}
        upsert_attributes(player[0], attrs)
        count += 1

    db.commit()
    print(f"Upserted {count} player attributes for {team_short}")
    return count
