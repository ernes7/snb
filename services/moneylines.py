"""Player moneyline generation — data-driven prop predictions per game."""
from __future__ import annotations

import json
from typing import Any

from db import get_db
from services.moneyline_signals import (
    SignalCandidate, load_lineup, batting_signals, pitching_signals,
    _player_name,
)

MIN_CONFIDENCE = 0.25
FALLBACK_CONFIDENCE = 0.15
BATTING_TYPES = {
    'hit_streak', 'xbh_streak', 'hr_power', 'rbi_hot',
    'sb_threat', 'batter_vs_opp',
}
PITCHING_TYPES = {'pitcher_k', 'pitcher_dom', 'pitcher_hr_vuln'}


def _select_top_3(candidates: list[SignalCandidate]) -> list[SignalCandidate]:
    """Pick the 3 most compelling, diverse moneylines from candidates."""
    candidates.sort(key=lambda c: c.confidence, reverse=True)
    selected: list[SignalCandidate] = []
    used_pids: set[int] = set()
    cat_counts = {"bat": 0, "pit": 0, "mat": 0}
    type_counts: dict[str, int] = {}

    def _cat(pt: str) -> str:
        if pt in BATTING_TYPES: return "bat"
        if pt in PITCHING_TYPES: return "pit"
        return "mat"

    for threshold in (MIN_CONFIDENCE, FALLBACK_CONFIDENCE):
        for c in candidates:
            if len(selected) >= 3:
                break
            if c.confidence < threshold:
                continue
            if c.player_id in used_pids:
                continue
            if type_counts.get(c.prop_type, 0) >= 2:
                continue
            cat = _cat(c.prop_type)
            if threshold == MIN_CONFIDENCE and cat_counts[cat] >= 2:
                continue
            selected.append(c)
            used_pids.add(c.player_id)
            cat_counts[cat] += 1
            type_counts[c.prop_type] = type_counts.get(c.prop_type, 0) + 1
        if len(selected) >= 3:
            break
    return selected


def generate_moneylines(week_num: int) -> list[dict[str, Any]]:
    """Generate 3 moneylines per unplayed game in the given week."""
    from services.weekly import _get_best_available_pitcher
    from blueprints.schedule.services import get_unavailable_pitchers

    db = get_db()
    unavailable = get_unavailable_pitchers()
    games = db.execute("""
        SELECT s.id as schedule_id, s.home_team_id, s.away_team_id
        FROM schedule s LEFT JOIN games g ON g.schedule_id = s.id
        WHERE s.phase = 'regular' AND s.week_num = ? AND g.id IS NULL
        ORDER BY s.game_num
    """, (week_num,)).fetchall()

    all_ml: list[dict[str, Any]] = []
    for game in games:
        sid = game["schedule_id"]
        h_tid, a_tid = game["home_team_id"], game["away_team_id"]
        _, _, h_sp_id = _get_best_available_pitcher(db, h_tid, week_num, unavailable)
        _, _, a_sp_id = _get_best_available_pitcher(db, a_tid, week_num, unavailable)

        candidates: list[SignalCandidate] = []
        for pid, name, tid, log, spd in load_lineup(db, h_tid):
            candidates.extend(batting_signals(
                sid, pid, tid, name, log, spd, a_tid, a_sp_id, db))
        for pid, name, tid, log, spd in load_lineup(db, a_tid):
            candidates.extend(batting_signals(
                sid, pid, tid, name, log, spd, h_tid, h_sp_id, db))
        if h_sp_id:
            candidates.extend(pitching_signals(
                sid, h_sp_id, h_tid, _player_name(db, h_sp_id), db, a_tid))
        if a_sp_id:
            candidates.extend(pitching_signals(
                sid, a_sp_id, a_tid, _player_name(db, a_sp_id), db, h_tid))

        for i, c in enumerate(_select_top_3(candidates), 1):
            all_ml.append({
                "schedule_id": sid, "player_id": c.player_id,
                "team_id": c.team_id, "prop_type": c.prop_type,
                "prop_text": c.prop_text,
                "stat_detail": json.dumps(c.stat_detail, ensure_ascii=False),
                "confidence": round(c.confidence, 4),
                "slot": i, "week_num": week_num,
            })
    return all_ml


def save_moneylines(week_num: int, moneylines: list[dict[str, Any]]) -> None:
    """Persist moneylines. Clears existing for the week first (idempotent)."""
    db = get_db()
    db.execute("DELETE FROM game_moneylines WHERE week_num = ?", (week_num,))
    for m in moneylines:
        db.execute("""
            INSERT INTO game_moneylines
                (schedule_id, player_id, team_id, prop_type, prop_text,
                 stat_detail, confidence, slot, week_num)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (m["schedule_id"], m["player_id"], m["team_id"], m["prop_type"],
              m["prop_text"], m["stat_detail"], m["confidence"], m["slot"],
              m["week_num"]))
    db.commit()
