"""Compare on-screen attribute readings against DB values.

Reads .scratch/attr_audit.md, which contains one line per player with the
values read from screenshots, and diffs them against player_attributes
for the matching DB row (team + normalized-name filename).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from db import get_db

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / ".scratch" / "attr_audit.md"

PITCH_KEY_TO_COL = {
    "R4C": "fastball",
    "SLD": "slider",
    "CRV": "curveball",
    "SNK": "sinker",
    "TND": "changeup",
    "SPL": "splitter",
    "SCR": "screwball",
    "CBB": "curveball_dirt",
    "RCT": "cutter",
    "CCL": "circle_changeup",
}

BATTER_LINE = re.compile(
    r"^(?P<team>[A-Z]{3})/(?P<file>[\w]+)\.png\s*\|\s*"
    r"(?P<pvl>\d+)\s+(?P<cvl>\d+)\s*\|\s*"
    r"(?P<pvr>\d+)\s+(?P<cvr>\d+)\s*\|\s*(?P<spd>\d+)\s*$"
)
PITCHER_LINE = re.compile(
    r"^(?P<team>[A-Z]{3})/(?P<file>[\w]+)\.png\s*\|\s*(?P<stm>\d+)\s*\|\s*(?P<rest>.+)$"
)


def unslugify(file_base: str) -> str:
    """Turn 'Y_Perez_11' back into 'Y. Perez' (jersey suffix dropped)."""
    parts = file_base.split("_")
    if parts[-1].isdigit():
        parts = parts[:-1]
    if not parts:
        return file_base
    first = parts[0] + "." if len(parts[0]) == 1 else parts[0]
    rest = " ".join(parts[1:])
    return f"{first} {rest}".strip()


def fetch_db_row(db, team: str, name: str) -> dict | None:
    for cand in (name, name + "."):
        row = db.execute("""
            SELECT p.name, p.role,
                a.power_vs_l, a.contact_vs_l, a.power_vs_r, a.contact_vs_r, a.speed,
                a.stamina, a.fastball, a.slider, a.curveball, a.sinker,
                a.changeup, a.splitter, a.screwball, a.cutter, a.curveball_dirt, a.circle_changeup
            FROM players p
            JOIN teams t ON p.team_id = t.id
            LEFT JOIN player_attributes a ON a.player_id = p.id
            WHERE t.short_name = ? AND p.name = ?
        """, (team, cand)).fetchall()
        if len(row) == 1:
            return dict(row[0])
        if len(row) > 1:
            print(f"  WARN: {team} {cand!r} has {len(row)} DB matches; skipping")
            return None
    return None


def fetch_db_row_by_role(db, team: str, name: str, role_guess: str) -> dict | None:
    """For ambiguous names (duplicate Y.Perez), pick by role category."""
    roles = (
        ("lineup", "bench") if role_guess == "batter" else ("rotation", "bullpen")
    )
    rows = db.execute("""
        SELECT p.name, p.role,
            a.power_vs_l, a.contact_vs_l, a.power_vs_r, a.contact_vs_r, a.speed,
            a.stamina, a.fastball, a.slider, a.curveball, a.sinker,
            a.changeup, a.splitter, a.screwball, a.cutter, a.curveball_dirt, a.circle_changeup
        FROM players p
        JOIN teams t ON p.team_id = t.id
        LEFT JOIN player_attributes a ON a.player_id = p.id
        WHERE t.short_name = ? AND p.name = ? AND p.role IN (?, ?)
    """, (team, name, *roles)).fetchall()
    if len(rows) == 1:
        return dict(rows[0])
    return None


def compare_batter(db_row: dict, seen: dict) -> list[str]:
    diffs = []
    mapping = {
        "power_vs_l": "pvl",
        "contact_vs_l": "cvl",
        "power_vs_r": "pvr",
        "contact_vs_r": "cvr",
        "speed": "spd",
    }
    for col, key in mapping.items():
        db_v = db_row.get(col)
        seen_v = int(seen[key])
        if db_v != seen_v:
            diffs.append(f"{col}: DB={db_v} SCREEN={seen_v}")
    return diffs


def parse_pitch_rest(rest: str) -> dict[str, int]:
    """Extract R4C=91 TND=81 ... pairs from the audit line."""
    pairs = {}
    for key, val in re.findall(r"(R4C|SLD|CRV|SNK|TND|SPL|SCR|CBB|RCT|CCL)=(\d+)", rest):
        pairs[PITCH_KEY_TO_COL[key]] = int(val)
    return pairs


def compare_pitcher(db_row: dict, stm: int, pitches: dict[str, int]) -> list[str]:
    diffs = []
    if db_row.get("stamina") != stm:
        diffs.append(f"stamina: DB={db_row.get('stamina')} SCREEN={stm}")
    for col, seen_v in pitches.items():
        db_v = db_row.get(col)
        if db_v != seen_v:
            diffs.append(f"{col}: DB={db_v} SCREEN={seen_v}")
    # Report pitches in DB but missing from screen (likely wrong column assigned)
    for col in PITCH_KEY_TO_COL.values():
        if col not in pitches and db_row.get(col) is not None:
            diffs.append(f"{col}: DB={db_row.get(col)} but NOT on screen")
    return diffs


def main() -> None:
    app = create_app()
    with app.app_context():
        db = get_db()
        current_section = ""
        total = 0
        mismatches = 0
        mismatch_report: list[tuple[str, str, list[str]]] = []

        for raw in AUDIT.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("## "):
                current_section = line[3:].lower()
                continue

            mb = BATTER_LINE.match(line)
            mp = PITCHER_LINE.match(line)

            if mb:
                team = mb.group("team")
                file_base = mb.group("file")
                db_name = unslugify(file_base)
                if file_base.endswith(("_11", "_56")):
                    db_row = fetch_db_row_by_role(db, team, db_name, "batter")
                else:
                    db_row = fetch_db_row(db, team, db_name)
                if not db_row:
                    print(f"MISS: {team}/{file_base} -> no DB row for {db_name!r}")
                    continue
                diffs = compare_batter(db_row, mb.groupdict())
                total += 1
                if diffs:
                    mismatches += 1
                    mismatch_report.append((team, db_row["name"], diffs))

            elif mp and "pitcher" in current_section:
                team = mp.group("team")
                file_base = mp.group("file")
                db_name = unslugify(file_base)
                stm = int(mp.group("stm"))
                pitches = parse_pitch_rest(mp.group("rest"))
                if file_base.endswith(("_11", "_56")):
                    db_row = fetch_db_row_by_role(db, team, db_name, "pitcher")
                else:
                    db_row = fetch_db_row(db, team, db_name)
                if not db_row:
                    print(f"MISS: {team}/{file_base} -> no DB row for {db_name!r}")
                    continue
                diffs = compare_pitcher(db_row, stm, pitches)
                total += 1
                if diffs:
                    mismatches += 1
                    mismatch_report.append((team, db_row["name"], diffs))

        print(f"\nAudited: {total}  Mismatches: {mismatches}")
        for team, name, diffs in mismatch_report:
            print(f"\n{team}  {name}")
            for d in diffs:
                print(f"  - {d}")


if __name__ == "__main__":
    main()
