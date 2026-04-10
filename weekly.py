"""Weekly summary generator — prints compact report for content generation."""
from __future__ import annotations

import sys
import os

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from app import create_app
from lib.utils import format_ip
from services.standings import get_standings
from services.weekly import (
    get_week_games,
    get_week_top_batters,
    get_week_top_pitchers,
    get_analysts_compact,
    _get_rank_map,
)


def print_weekly_summary(week_num: int) -> None:
    """Print a compact weekly summary to stdout."""
    games = get_week_games(week_num)
    if not games:
        print(f"No games found for week {week_num}.")
        return

    start_gnum = (week_num - 1) * 4 + 1
    end_gnum = week_num * 4
    print(f"=== SEMANA {week_num} (Juegos {start_gnum}-{end_gnum}) ===\n")

    # Results
    print("RESULTADOS:")
    for g in games:
        winner = g["home_short"] if g["home_runs"] > g["away_runs"] else g["away_short"]
        loser = g["away_short"] if winner == g["home_short"] else g["home_short"]
        w_runs = max(g["home_runs"], g["away_runs"])
        l_runs = min(g["home_runs"], g["away_runs"])
        sv = f" SV:{g['sv_name']}" if g["sv_name"] else ""
        print(f"  G{g['game_num']}: {winner} {w_runs}-{l_runs} {loser}"
              f"  W:{g['wp_name']} L:{g['lp_name']}{sv}")
        if g["home_linescore"] or g["away_linescore"]:
            h_ls = g["home_linescore"] or ""
            a_ls = g["away_linescore"] or ""
            print(f"    {g['home_short']}: {h_ls}")
            print(f"    {g['away_short']}: {a_ls}")

    # Standings
    print("\nCLASIFICACION:")
    standings = get_standings()
    for i, s in enumerate(standings, 1):
        diff = f"+{s['diff']}" if s["diff"] > 0 else str(s["diff"])
        print(f"  {i}. {s['short_name']} {s['wins']}-{s['losses']}"
              f" {s['pct']} ({diff})")

    # Top batters
    print("\nTOP BATEADORES SEMANA:")
    batters = get_week_top_batters(week_num, limit=5)
    for b in batters:
        extras = []
        if b["HR"]:
            extras.append(f"{b['HR']} HR")
        if b["triples"]:
            extras.append(f"{b['triples']} 3B")
        if b["doubles"]:
            extras.append(f"{b['doubles']} 2B")
        if b["RBI"]:
            extras.append(f"{b['RBI']}RBI")
        if b["R"]:
            extras.append(f"{b['R']}R")
        if b["SB"]:
            extras.append(f"{b['SB']}SB")
        extra_str = " " + " ".join(extras) if extras else ""
        print(f"  {b['name']}({b['short_name']}) {b['H']}-{b['AB']}{extra_str}"
              f" AVG:{b['AVG']}")

    # Top pitchers
    print("\nTOP LANZADORES SEMANA:")
    pitchers = get_week_top_pitchers(week_num, limit=5)
    for p in pitchers:
        ip = format_ip(p["IP_outs"])
        record = []
        if p["W"]:
            record.append(f"{p['W']}W")
        if p["L"]:
            record.append(f"{p['L']}L")
        if p["SV"]:
            record.append(f"{p['SV']}SV")
        rec_str = " " + " ".join(record) if record else ""
        era = round(p["ER"] * 9 / max(p["IP_outs"] / 3, 0.01), 2)
        print(f"  {p['name']}({p['short_name']}) {ip}IP {p['H']}H"
              f" {p['ER']}ER {p['SO']}SO ERA:{era}{rec_str}")

    # Analysts
    print("\nANALISTAS:")
    for a in get_analysts_compact():
        fav = a["fav_team"] or "?"
        hate = a["hate_team"] or "?"
        emoji = a["emoji"] or ""
        try:
            print(f"  @{a['handle']}: {emoji} estilo={a['estilo']},"
                  f" fav={fav}, odia={hate}, frase=\"{a['frase']}\"")
        except UnicodeEncodeError:
            print(f"  @{a['handle']}: estilo={a['estilo']},"
                  f" fav={fav}, odia={hate}, frase=\"{a['frase']}\"")

    # Upcoming games (next week) with power rankings for predictions
    from db import get_db
    next_week = week_num + 1
    db = get_db()
    upcoming = db.execute("""
        SELECT s.game_num, s.id as schedule_id,
            ht.short_name as home, at.short_name as away
        FROM schedule s
        JOIN teams ht ON s.home_team_id = ht.id
        JOIN teams at ON s.away_team_id = at.id
        WHERE s.phase = 'regular' AND s.week_num = ?
        ORDER BY s.game_num
    """, (next_week,)).fetchall()
    if upcoming:
        rank_map = _get_rank_map(week_num)
        short_to_rank = {}
        for row in db.execute("SELECT id, short_name FROM teams").fetchall():
            short_to_rank[row["short_name"]] = rank_map.get(row["id"], "?")
        print(f"\nPROXIMA SEMANA {next_week} (para predicciones):")
        for g in upcoming:
            hr = short_to_rank.get(g["home"], "?")
            ar = short_to_rank.get(g["away"], "?")
            print(f"  G{g['game_num']}: {g['home']}(#{hr}) vs {g['away']}(#{ar})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python weekly.py <week_num>")
        sys.exit(1)

    week = int(sys.argv[1])
    app = create_app()
    with app.app_context():
        print_weekly_summary(week)
