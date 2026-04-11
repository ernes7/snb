"""Apply on-screen attribute values as corrections to the VCL player_attributes
rows. Dry-run by default — pass --apply to actually write.

Source of truth: .scratch/attr_audit.md readings.

The script re-uses the audit parser from audit_attributes.py so the logic
stays in one place.
"""
from __future__ import annotations

import re
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
TEAM = "VCL"


def resolve_player_id(db, team: str, file_base: str) -> int | None:
    """Find the player id for a given crop filename (team + normalized name)."""
    name = unslugify(file_base)
    if file_base.endswith("_11") or file_base.endswith("_56"):
        # Disambiguate by role group
        roles = ("lineup", "bench") if file_base.endswith("_11") else ("rotation", "bullpen")
        row = db.execute("""
            SELECT p.id FROM players p JOIN teams t ON p.team_id=t.id
            WHERE t.short_name=? AND p.name=? AND p.role IN (?,?)
        """, (team, name, *roles)).fetchone()
    else:
        row = db.execute("""
            SELECT p.id FROM players p JOIN teams t ON p.team_id=t.id
            WHERE t.short_name=? AND p.name=?
        """, (team, name)).fetchone()
    return row["id"] if row else None


def fetch_current(db, player_id: int) -> dict:
    row = db.execute("""
        SELECT power_vs_l, contact_vs_l, power_vs_r, contact_vs_r, speed,
               stamina, fastball, slider, curveball, sinker, changeup,
               splitter, screwball, cutter, curveball_dirt
        FROM player_attributes WHERE player_id=?
    """, (player_id,)).fetchone()
    return dict(row) if row else {}


def main(apply: bool) -> None:
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

            if mb and mb.group("team") == TEAM:
                file_base = mb.group("file")
                pid = resolve_player_id(db, TEAM, file_base)
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

            elif mp and mp.group("team") == TEAM and "pitcher" in current_section:
                file_base = mp.group("file")
                pid = resolve_player_id(db, TEAM, file_base)
                if not pid:
                    print(f"MISS: {file_base}")
                    continue
                pitches = parse_pitch_rest(mp.group("rest"))
                new_vals: dict[str, int] = {"stamina": int(mp.group("stm"))}
                for col in PITCH_KEY_TO_COL.values():
                    new_vals[col] = pitches.get(col)  # may be None → reset
                planned.append((pid, file_base, new_vals))

        # Diff summary
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

        print(f"\nTotal field changes: {total_changes}")

        if not apply:
            print("\nDry run. Re-run with --apply to write to DB.")
            return

        # Apply updates
        for pid, _, new_vals in planned:
            set_clause = ", ".join(f"{k}=?" for k in new_vals)
            values = list(new_vals.values()) + [pid]
            db.execute(
                f"UPDATE player_attributes SET {set_clause} WHERE player_id=?",
                values,
            )
        db.commit()
        print(f"\nApplied {len(planned)} row updates.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
