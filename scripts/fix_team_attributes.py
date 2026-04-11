"""Apply on-screen attribute values as corrections for a given team.

Usage:
    python scripts/fix_team_attributes.py GRA          # dry run
    python scripts/fix_team_attributes.py GRA --apply  # write to DB

Source of truth: .scratch/attr_audit.md readings.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from db import get_db
from scripts.audit_attributes import (
    BATTER_LINE,
    PITCHER_LINE,
    PITCH_KEY_TO_COL,
    parse_pitch_rest,
    unslugify,
)

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / ".scratch" / "attr_audit.md"


def resolve_player_id(db, team: str, file_base: str) -> int | None:
    name = unslugify(file_base)
    # Candidates — handle trailing period (e.g., "Jr.", "Jr CF") stripped by slugify
    candidates = [name, name + "."]
    for cand in candidates:
        if file_base.endswith("_11") or file_base.endswith("_56"):
            roles = ("lineup", "bench") if file_base.endswith("_11") else ("rotation", "bullpen")
            row = db.execute("""
                SELECT p.id FROM players p JOIN teams t ON p.team_id=t.id
                WHERE t.short_name=? AND p.name=? AND p.role IN (?,?)
            """, (team, cand, *roles)).fetchone()
        else:
            row = db.execute("""
                SELECT p.id FROM players p JOIN teams t ON p.team_id=t.id
                WHERE t.short_name=? AND p.name=?
            """, (team, cand)).fetchone()
        if row:
            return row["id"]
    return None


def fetch_current(db, player_id: int) -> dict:
    row = db.execute("""
        SELECT power_vs_l, contact_vs_l, power_vs_r, contact_vs_r, speed,
               stamina, fastball, slider, curveball, sinker, changeup,
               splitter, screwball, cutter, curveball_dirt, circle_changeup
        FROM player_attributes WHERE player_id=?
    """, (player_id,)).fetchone()
    return dict(row) if row else {}


def main(team: str, apply: bool) -> None:
    app = create_app()
    with app.app_context():
        db = get_db()
        current_section = ""
        planned: list[tuple[int, str, dict]] = []

        for raw in AUDIT.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("## "):
                current_section = line[3:].lower()
                continue

            mb = BATTER_LINE.match(line)
            mp = PITCHER_LINE.match(line)

            if mb and mb.group("team") == team:
                file_base = mb.group("file")
                pid = resolve_player_id(db, team, file_base)
                if not pid:
                    print(f"MISS: {file_base}")
                    continue
                new_vals = {
                    "power_vs_l": int(mb.group("pvl")),
                    "contact_vs_l": int(mb.group("cvl")),
                    "power_vs_r": int(mb.group("pvr")),
                    "contact_vs_r": int(mb.group("cvr")),
                    "speed": int(mb.group("spd")),
                }
                planned.append((pid, file_base, new_vals))

            elif mp and mp.group("team") == team and "pitcher" in current_section:
                file_base = mp.group("file")
                pid = resolve_player_id(db, team, file_base)
                if not pid:
                    print(f"MISS: {file_base}")
                    continue
                pitches = parse_pitch_rest(mp.group("rest"))
                new_vals: dict[str, int | None] = {"stamina": int(mp.group("stm"))}
                for col in PITCH_KEY_TO_COL.values():
                    new_vals[col] = pitches.get(col)  # None clears
                planned.append((pid, file_base, new_vals))

        total_changes = 0
        for pid, file_base, new_vals in planned:
            current = fetch_current(db, pid)
            changes = [(k, current.get(k), v) for k, v in new_vals.items()
                       if current.get(k) != v]
            if not changes:
                continue
            total_changes += len(changes)
            print(f"\n{file_base}")
            for col, old, new in changes:
                print(f"  {col}: {old} -> {new}")

        print(f"\n[{team}] rows planned: {len(planned)}  field changes: {total_changes}")

        if not apply:
            print("Dry run. Re-run with --apply to write.")
            return

        for pid, _, new_vals in planned:
            set_clause = ", ".join(f"{k}=?" for k in new_vals)
            values = list(new_vals.values()) + [pid]
            db.execute(
                f"UPDATE player_attributes SET {set_clause} WHERE player_id=?",
                values,
            )
        db.commit()
        print(f"Applied {len(planned)} row updates for {team}.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print("Usage: fix_team_attributes.py <TEAM> [--apply]")
        sys.exit(1)
    main(args[0].upper(), "--apply" in sys.argv)
