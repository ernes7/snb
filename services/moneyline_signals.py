"""Signal detectors for player moneylines — private module."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from lib.stats import BattingLine, PitchingLine
from lib.utils import format_ip

RECENT_WINDOW = 5


@dataclass
class SignalCandidate:
    schedule_id: int
    player_id: int
    team_id: int
    prop_type: str
    prop_text: str
    stat_detail: dict
    confidence: float


def _sample_mult(n: int) -> float:
    if n >= 7: return 1.0
    if n >= 5: return 0.95
    if n >= 4: return 0.85
    if n >= 3: return 0.75
    if n >= 2: return 0.6
    return 0.4


def _streak_len(log: list[dict], pred) -> int:
    count = 0
    for g in reversed(log):
        if pred(g):
            count += 1
        else:
            break
    return count


def _team_short(db: sqlite3.Connection, tid: int) -> str:
    r = db.execute("SELECT short_name FROM teams WHERE id=?", (tid,)).fetchone()
    return r["short_name"] if r else "???"


def _player_name(db: sqlite3.Connection, pid: int) -> str:
    r = db.execute("SELECT name FROM players WHERE id=?", (pid,)).fetchone()
    return r["name"] if r else "???"


def load_lineup(db: sqlite3.Connection, team_id: int):
    """Load lineup batters with game logs and speed attribute.

    Returns list of (player_id, name, team_id, log, speed) tuples.
    """
    players = db.execute("""
        SELECT p.id, p.name, p.team_id, COALESCE(pa.speed, 0) as speed
        FROM players p
        LEFT JOIN player_attributes pa ON pa.player_id = p.id
        WHERE p.team_id = ? AND p.role = 'lineup'
        ORDER BY p.lineup_order
    """, (team_id,)).fetchall()
    result = []
    for p in players:
        log = db.execute("""
            SELECT bs.AB, bs.H, bs.doubles, bs.triples, bs.HR,
                bs.RBI, bs.BB, bs.SO, bs.SB, bs.R
            FROM batting_stats bs
            JOIN games g ON bs.game_id = g.id
            JOIN schedule s ON g.schedule_id = s.id
            WHERE bs.player_id = ? ORDER BY s.game_num
        """, (p["id"],)).fetchall()
        result.append((p["id"], p["name"], p["team_id"],
                        [dict(r) for r in log], p["speed"]))
    return result


def batting_signals(
    sid: int, pid: int, tid: int, name: str,
    log: list[dict], speed: int,
    opp_tid: int, opp_starter_id: int | None,
    db: sqlite3.Connection,
) -> list[SignalCandidate]:
    """Run all batting signal detectors for one batter."""
    if not log:
        return []
    out: list[SignalCandidate] = []
    n = len(log)
    sm = _sample_mult(n)
    recent = log[-RECENT_WINDOW:]

    streak = _streak_len(log, lambda g: g["H"] > 0)
    if streak >= 3:
        hits = sum(g["H"] for g in log[-streak:])
        drama = 1.15 if streak == n else 1.0
        conf = min(streak / 7, 1.0) * sm * drama
        out.append(SignalCandidate(sid, pid, tid, "hit_streak",
            f"{name}: racha de {streak} juegos con hit ({hits} H)",
            {"streak": streak, "hits": hits}, conf))

    streak = _streak_len(log, lambda g: g["doubles"] + g["triples"] + g["HR"] > 0)
    if streak >= 2:
        xbh = sum(g["doubles"] + g["triples"] + g["HR"] for g in log[-streak:])
        conf = min(streak / 5, 1.0) * sm * 1.1
        out.append(SignalCandidate(sid, pid, tid, "xbh_streak",
            f"{name}: XBH en {streak} juegos seguidos ({xbh} XBH)",
            {"streak": streak, "xbh": xbh}, conf))

    hr = sum(g["HR"] for g in recent)
    if hr >= 2:
        total_hr = sum(g["HR"] for g in log)
        multi = any(g["HR"] >= 2 for g in recent)
        conf = min(hr / (len(recent) * 0.5), 1.0) * sm * (1.15 if multi else 1.0)
        out.append(SignalCandidate(sid, pid, tid, "hr_power",
            f"{name}: {hr} HR en {len(recent)} juegos ({total_hr} total)",
            {"recent_hr": hr, "total_hr": total_hr}, conf))

    rbi = sum(g["RBI"] for g in recent)
    if rbi >= 4:
        conf = min(rbi / (len(recent) * 2.0), 1.0) * sm
        out.append(SignalCandidate(sid, pid, tid, "rbi_hot",
            f"{name}: {rbi} CE en ultimos {len(recent)} juegos",
            {"rbi": rbi, "games": len(recent)}, conf))

    sb = sum(g["SB"] for g in recent)
    if speed >= 75 and sb >= 1:
        conf = min(sb / 3, 1.0) * (speed / 99) * sm
        out.append(SignalCandidate(sid, pid, tid, "sb_threat",
            f"{name}: {sb} BR en {len(recent)} juegos (vel: {speed})",
            {"sb": sb, "speed": speed}, conf))

    h2h = _h2h_batting(db, pid, opp_tid)
    if h2h and h2h["AB"] >= 6 and h2h["games"] >= 2:
        line = BattingLine.from_row(h2h)
        if line.AVG >= 0.300:
            opp = _team_short(db, opp_tid)
            hr_s = f" con {h2h['HR']} HR" if h2h["HR"] else ""
            conf = min((line.AVG - 0.2) / 0.3, 1.0) * 0.85 * _sample_mult(h2h["games"]) * 1.1
            out.append(SignalCandidate(sid, pid, tid, "batter_vs_opp",
                f"{name}: .{int(line.AVG * 1000):03d} ({h2h['H']}-{h2h['AB']}{hr_s}) vs {opp}",
                {"avg": round(line.AVG, 3), "ab": h2h["AB"], "hr": h2h["HR"]}, conf))

    if opp_starter_id:
        bvp = _batter_vs_pitcher(db, pid, opp_starter_id)
        if bvp and bvp["AB"] >= 5 and (bvp["H"] / bvp["AB"] >= 0.333 or bvp["HR"]):
            sname = _player_name(db, opp_starter_id)
            hr_s = f" con {bvp['HR']} HR" if bvp["HR"] else ""
            strength = max(min((bvp["H"] / bvp["AB"] - 0.2) / 0.3, 1.0),
                           0.6 if bvp["HR"] else 0.0)
            conf = strength * _sample_mult(bvp["AB"]) * 1.2
            out.append(SignalCandidate(sid, pid, tid, "batter_vs_pitcher",
                f"{name}: {bvp['H']}-{bvp['AB']}{hr_s} vs {sname}",
                {"ab": bvp["AB"], "h": bvp["H"], "hr": bvp["HR"]}, conf))

    return out


def _h2h_batting(db: sqlite3.Connection, player_id: int, opp_tid: int):
    row = db.execute("""
        SELECT COUNT(DISTINCT bs.game_id) as games,
            SUM(bs.AB) as AB, SUM(bs.H) as H,
            SUM(bs.doubles) as doubles, SUM(bs.triples) as triples,
            SUM(bs.HR) as HR, SUM(bs.RBI) as RBI,
            SUM(bs.BB) as BB, SUM(bs.SO) as SO, SUM(bs.SB) as SB
        FROM batting_stats bs
        JOIN games g ON bs.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        WHERE bs.player_id = ?
          AND (s.home_team_id = ? OR s.away_team_id = ?)
    """, (player_id, opp_tid, opp_tid)).fetchone()
    return dict(row) if row and row["AB"] else None


def _batter_vs_pitcher(db: sqlite3.Connection, batter_id: int, pitcher_id: int):
    row = db.execute("""
        SELECT SUM(bs.AB) as AB, SUM(bs.H) as H,
            SUM(bs.doubles) as doubles, SUM(bs.triples) as triples,
            SUM(bs.HR) as HR, SUM(bs.RBI) as RBI,
            SUM(bs.BB) as BB, SUM(bs.SO) as SO, SUM(bs.SB) as SB
        FROM batting_stats bs
        JOIN pitching_stats ps ON bs.game_id = ps.game_id
        WHERE bs.player_id = ? AND ps.player_id = ?
          AND ps.IP_outs >= 15 AND bs.team_id != ps.team_id
    """, (batter_id, pitcher_id)).fetchone()
    return dict(row) if row and row["AB"] else None


def pitching_signals(
    sid: int, pid: int, tid: int, name: str,
    db: sqlite3.Connection, opp_tid: int,
) -> list[SignalCandidate]:
    """Run pitcher signal detectors for a probable starter."""
    rows = db.execute("""
        SELECT ps.IP_outs, ps.H, ps.R, ps.ER, ps.BB, ps.SO,
            ps.HR_allowed, ps.W, ps.L, ps.SV
        FROM pitching_stats ps
        JOIN games g ON ps.game_id = g.id
        JOIN schedule s ON g.schedule_id = s.id
        WHERE ps.player_id = ? ORDER BY s.game_num
    """, (pid,)).fetchall()
    if not rows:
        return []
    log = [dict(r) for r in rows]
    out: list[SignalCandidate] = []
    sm = _sample_mult(len(log))
    totals = {k: sum(g[k] for g in log) for k in log[0]}
    career = PitchingLine.from_row(totals)

    if career.IP_outs >= 9 and career.K9 >= 6.0:
        conf = min((career.K9 - 4.0) / 8.0, 1.0) * sm
        out.append(SignalCandidate(sid, pid, tid, "pitcher_k",
            f"{name}: {career.K9:.1f} K/9 en {format_ip(career.IP_outs)} IP ({career.SO} SO)",
            {"k9": round(career.K9, 1), "so": career.SO}, conf))

    scoreless = 0
    for g in reversed(log):
        if g["ER"] == 0:
            scoreless += g["IP_outs"]
        else:
            break
    if scoreless >= 12:
        conf = min(scoreless / 27, 1.0) * sm * 1.15
        out.append(SignalCandidate(sid, pid, tid, "pitcher_dom",
            f"{name}: {format_ip(scoreless)} IP sin carrera limpia",
            {"scoreless_outs": scoreless}, conf))

    last3 = log[-3:]
    hr_a = sum(g["HR_allowed"] for g in last3)
    ip_o = sum(g["IP_outs"] for g in last3)
    if hr_a >= 3 and ip_o > 0:
        opp = _team_short(db, opp_tid)
        conf = min((hr_a * 27 / ip_o) / 3.0, 1.0) * sm
        out.append(SignalCandidate(sid, pid, tid, "pitcher_hr_vuln",
            f"{name}: {hr_a} HR en {format_ip(ip_o)} IP vs {opp}",
            {"hr_allowed": hr_a, "ip_outs": ip_o}, conf))

    return out
