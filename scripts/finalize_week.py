"""Finalize a completed week's content.

Given week N (the week just completed), this script:

  1. Runs the deterministic auto-generation (rankings for N, picks + GotW for N+1)
     so those pieces are persisted immediately.
  2. Prints POTW candidates, the current rankings skeleton with BLANK blurbs
     flagged, and ready-to-paste call templates for the pieces that still need
     creative content (blurbs, POTW summary, 3 weekly analyses).

Usage:
    python scripts/finalize_week.py <week_num>

Nothing creative is saved — only the deterministic data. You paste blurbs
and run `save_weekly_awards` / `save_weekly_tweets` yourself.
"""
from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from db import get_db
from lib.utils import format_ip
from services.weekly import (
    auto_generate_week,
    can_auto_generate,
    get_week_top_batters,
    get_week_top_pitchers,
    week_completion_status,
)


def _short_map() -> dict[int, str]:
    db = get_db()
    return {r["id"]: r["short_name"] for r in db.execute("SELECT id, short_name FROM teams")}


def _print_potw_candidates(week_num: int) -> None:
    print("POTW CANDIDATES (top of week):")
    print("  batters:")
    for b in get_week_top_batters(week_num, limit=5):
        extras = []
        if b["HR"]:
            extras.append(f"{b['HR']}HR")
        if b["RBI"]:
            extras.append(f"{b['RBI']}RBI")
        if b["R"]:
            extras.append(f"{b['R']}R")
        if b["SB"]:
            extras.append(f"{b['SB']}SB")
        extra_str = " " + " ".join(extras) if extras else ""
        print(f"    id={b['id']:>3}  {b['name']}({b['short_name']})"
              f"  {b['H']}-{b['AB']}{extra_str}  AVG={b['AVG']}")
    print("  pitchers:")
    for p in get_week_top_pitchers(week_num, limit=5):
        ip = format_ip(p["IP_outs"])
        rec = []
        if p["W"]:
            rec.append(f"{p['W']}W")
        if p["L"]:
            rec.append(f"{p['L']}L")
        if p["SV"]:
            rec.append(f"{p['SV']}SV")
        rec_str = " " + " ".join(rec) if rec else ""
        era = round(p["ER"] * 9 / max(p["IP_outs"] / 3, 0.01), 2)
        print(f"    id={p['id']:>3}  {p['name']}({p['short_name']})"
              f"  {ip}IP {p['ER']}ER {p['SO']}SO  ERA={era}{rec_str}")


def _print_rankings_skeleton(week_num: int) -> None:
    """Print the week's auto-generated rankings with blurb slots empty."""
    db = get_db()
    row = db.execute(
        "SELECT power_rankings FROM weekly_awards WHERE week_num = ?",
        (week_num,),
    ).fetchone()
    if not row or not row["power_rankings"]:
        print(f"(no rankings persisted for week {week_num})")
        return
    rankings = json.loads(row["power_rankings"])
    shorts = _short_map()
    print(f"RANKINGS SKELETON (week {week_num}) — fill each blurb before saving:")
    for r in rankings:
        short = shorts.get(r["team_id"], "?")
        prev = r.get("prev_rank")
        prev_s = f"prev#{prev}" if prev else "new"
        blurb = r.get("blurb") or ""
        flag = "" if blurb else "  <-- BLANK"
        print(f"  #{r['rank']} {short:>4}  score={r['score']:.4f}  ({prev_s}){flag}")
        if blurb:
            print(f"      blurb: {blurb[:90]}{'...' if len(blurb) > 90 else ''}")


def _print_save_template(week_num: int) -> None:
    print("NEXT STEPS (run inside `with create_app().app_context():`):\n")
    print("  # 1. Finalize rankings + POTW (fill blurbs, then save):")
    print("  from services.weekly import save_weekly_awards, save_weekly_tweets")
    print("  from services.power_rankings import compute_power_rankings")
    print(f"  rankings = compute_power_rankings({week_num})")
    print("  for r in rankings:")
    print("      r['blurb'] = '...'  # 1-2 sentences per team")
    print(f"  save_weekly_awards(week_num={week_num}, potw_player_id=<id>,")
    print("                     potw_summary='...', power_rankings=rankings,")
    print(f"                     game_of_week_id=<sched_id or None>)\n")
    print("  # 2. Weekly analyses (3 pieces, 4 sentences each — NOT tweets):")
    print(f"  save_weekly_tweets({week_num}, [")
    print("      {'analyst_id': 1, 'texto': '...'},  # Panfilo")
    print("      {'analyst_id': 2, 'texto': '...'},  # Chequera")
    print("      {'analyst_id': 3, 'texto': '...'},  # Facundo")
    print("  ])")


def main(week_num: int) -> None:
    status = week_completion_status(week_num)
    if status["total"] == 0:
        print(f"Week {week_num} does not exist in schedule.")
        sys.exit(1)
    if status["boxscored"] < status["total"]:
        print(f"Week {week_num} not fully boxscored "
              f"({status['boxscored']}/{status['total']}). Enter remaining games first.")
        sys.exit(1)

    next_week = week_num + 1
    print(f"=== FINALIZING WEEK {week_num} ===\n")

    allowed, reason = can_auto_generate(next_week)
    if allowed:
        result = auto_generate_week(next_week)
        gotw = result["game_of_week_id"]
        print(f"[auto] rankings for W{week_num} persisted "
              f"({result['rankings_count']} teams)")
        print(f"[auto] picks for W{next_week} saved "
              f"({result['picks_count']} rows)")
        print(f"[auto] Game of the Week for W{next_week} = schedule_id {gotw}")
        ml_count = result.get("moneylines_count", 0)
        print(f"[auto] moneylines for W{next_week} saved "
              f"({ml_count} props across {ml_count // 3} games)\n")
    else:
        print(f"[skip auto] {reason}\n")

    _print_potw_candidates(week_num)
    print()
    _print_rankings_skeleton(week_num)
    print()
    _print_save_template(week_num)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/finalize_week.py <week_num>")
        sys.exit(1)
    app = create_app()
    with app.app_context():
        main(int(sys.argv[1]))
