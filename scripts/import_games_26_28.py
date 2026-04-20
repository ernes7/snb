"""Import games 26, 27, 28 (week 7)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from services.game_import import insert_game


# ============ GAME 26: VCL 3, SSP 0 ============
GAME26_BATTING = [
    # VCL (away) — 9-inning shutout; Perez CG
    {"name": "R. Lunar",    "team": "VCL", "AB": 5, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "A. Zamora",   "team": "VCL", "AB": 5, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "Y. Garcia",   "team": "VCL", "AB": 4, "R": 1, "H": 2, "2B": 1, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "A. Borrero",  "team": "VCL", "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "A. Pestano",  "team": "VCL", "AB": 4, "R": 0, "H": 2, "2B": 1, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 0, "SB": 0},
    {"name": "Y. Vido",     "team": "VCL", "AB": 4, "R": 0, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "Y. Canto",    "team": "VCL", "AB": 4, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "Y. Diaz",     "team": "VCL", "AB": 4, "R": 0, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "E. Paret",    "team": "VCL", "AB": 4, "R": 1, "H": 3, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    # SSP (home)
    {"name": "F. Cepeda",      "team": "SSP", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 3, "SB": 0},
    {"name": "Y. Mendoza",     "team": "SSP", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "Y. Ibanez",      "team": "SSP", "AB": 4, "R": 0, "H": 3, "2B": 1, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "D. Moreira",     "team": "SSP", "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "Y. Gourriel",    "team": "SSP", "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "L. Gourriel Jr", "team": "SSP", "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2, "SB": 0},
    {"name": "E. Sanchez",     "team": "SSP", "AB": 3, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "Y. Gourriel CF", "team": "SSP", "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2, "SB": 0},
    {"name": "Y. Bello",       "team": "SSP", "AB": 3, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
]
GAME26_PITCHING = [
    {"name": "Y. Perez",  "team": "VCL", "IP": "9.0", "H": 7, "R": 0, "ER": 0, "BB": 0, "SO": 7, "HR": 0, "W": 1, "L": 0, "SV": 0, "pitches": 94},
    {"name": "Y. Panama", "team": "SSP", "IP": "5.1", "H": 8, "R": 2, "ER": 2, "BB": 0, "SO": 2, "HR": 0, "W": 0, "L": 1, "SV": 0, "pitches": 49},
    {"name": "O. Luis Jr","team": "SSP", "IP": "3.2", "H": 6, "R": 1, "ER": 1, "BB": 0, "SO": 0, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 29},
]


# ============ GAME 27: CAV 3, PRI 2 ============
GAME27_BATTING = [
    # CAV (away) — 2 HRs won it
    {"name": "A. Sanchez",  "team": "CAV", "AB": 5, "R": 1, "H": 2, "2B": 1, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "M. Enriquez", "team": "CAV", "AB": 4, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 1, "RBI": 2, "BB": 0, "SO": 1, "SB": 0},
    {"name": "Y. Charles",  "team": "CAV", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "Y. Fiss",     "team": "CAV", "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "M. Vega",     "team": "CAV", "AB": 4, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 1, "RBI": 1, "BB": 0, "SO": 1, "SB": 0},
    {"name": "I. Martinez", "team": "CAV", "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "Y. Borroto",  "team": "CAV", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "A. Civil",    "team": "CAV", "AB": 4, "R": 0, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "L. Diaz",     "team": "CAV", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    # PRI (home)
    {"name": "Y. Cerce",        "team": "PRI", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2, "SB": 0},
    {"name": "D. Duarte",       "team": "PRI", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 1, "SO": 1, "SB": 0},
    {"name": "O. Del Rosario",  "team": "PRI", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2, "SB": 0},
    {"name": "D. Castillo",     "team": "PRI", "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "N. Concepcion",   "team": "PRI", "AB": 4, "R": 1, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "Y. Peraza",       "team": "PRI", "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2, "SB": 0},
    {"name": "R. Leon",         "team": "PRI", "AB": 4, "R": 1, "H": 1, "2B": 0, "3B": 1, "HR": 0, "RBI": 1, "BB": 0, "SO": 0, "SB": 0},
    {"name": "M. Rivera",       "team": "PRI", "AB": 3, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 0, "SB": 0},
    {"name": "L. Blanco",       "team": "PRI", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2, "SB": 0},
]
GAME27_PITCHING = [
    {"name": "A. Mora",      "team": "CAV", "IP": "3.1", "H": 4, "R": 0, "ER": 0, "BB": 1, "SO": 7, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 49},
    {"name": "V. Baro",      "team": "CAV", "IP": "5.1", "H": 4, "R": 2, "ER": 2, "BB": 0, "SO": 3, "HR": 0, "W": 1, "L": 0, "SV": 0, "pitches": 49},
    {"name": "E. Veliz",     "team": "CAV", "IP": "0.1", "H": 0, "R": 0, "ER": 0, "BB": 0, "SO": 1, "HR": 0, "W": 0, "L": 0, "SV": 1, "pitches": 6},
    {"name": "G. Miranda Jr.","team": "PRI","IP": "6.0", "H": 3, "R": 0, "ER": 0, "BB": 0, "SO": 4, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 53},
    {"name": "Y. Torres",    "team": "PRI", "IP": "1.2", "H": 4, "R": 3, "ER": 3, "BB": 0, "SO": 0, "HR": 2, "W": 0, "L": 1, "SV": 0, "pitches": 19},
    {"name": "A. Martinez",  "team": "PRI", "IP": "1.1", "H": 2, "R": 0, "ER": 0, "BB": 0, "SO": 2, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 18},
]


# ============ GAME 28: SCU 6, LTU 3 (10 innings) ============
GAME28_BATTING = [
    # SCU (away) — 3 runs in top 10
    {"name": "H. Olivera",     "team": "SCU", "AB": 5, "R": 1, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "R. Hurtado",     "team": "SCU", "AB": 5, "R": 3, "H": 3, "2B": 1, "3B": 0, "HR": 1, "RBI": 1, "BB": 0, "SO": 1, "SB": 0},
    {"name": "A. Bell",        "team": "SCU", "AB": 5, "R": 1, "H": 2, "2B": 1, "3B": 0, "HR": 0, "RBI": 2, "BB": 0, "SO": 0, "SB": 0},
    {"name": "J. Abreu",       "team": "SCU", "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 0, "SB": 0},
    {"name": "R. Merino",      "team": "SCU", "AB": 5, "R": 1, "H": 2, "2B": 1, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 1, "SB": 0},
    {"name": "P. Poll",        "team": "SCU", "AB": 5, "R": 0, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 1, "SB": 0},
    {"name": "L. Nava",        "team": "SCU", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 1, "SO": 0, "SB": 0},
    {"name": "R. Orta",        "team": "SCU", "AB": 5, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "M. Castellanos", "team": "SCU", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    # LTU (home) — walked off with 3 in bottom 10... wait no, SCU won. LTU couldn't score in 10th
    {"name": "G. Duvergel", "team": "LTU", "AB": 4, "R": 0, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "J. Pedroso",  "team": "LTU", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "Y. Scull",    "team": "LTU", "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "A. Quiala",   "team": "LTU", "AB": 4, "R": 2, "H": 3, "2B": 0, "3B": 0, "HR": 1, "RBI": 1, "BB": 0, "SO": 0, "SB": 3},
    {"name": "D. Castro",   "team": "LTU", "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "Y. Alarcon",  "team": "LTU", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "O. Arias",    "team": "LTU", "AB": 4, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 1, "RBI": 1, "BB": 0, "SO": 1, "SB": 0},
    {"name": "J. Johnson",  "team": "LTU", "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "A. Guerrero", "team": "LTU", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
]
GAME28_PITCHING = [
    {"name": "Y. Sanchez",  "team": "SCU", "IP": "5.0", "H": 4, "R": 2, "ER": 2, "BB": 0, "SO": 1, "HR": 2, "W": 0, "L": 0, "SV": 0, "pitches": 49},
    {"name": "A. Dela",     "team": "SCU", "IP": "4.2", "H": 5, "R": 1, "ER": 1, "BB": 0, "SO": 3, "HR": 0, "W": 1, "L": 0, "SV": 0, "pitches": 39},
    {"name": "O. Romero",   "team": "SCU", "IP": "0.1", "H": 0, "R": 0, "ER": 0, "BB": 0, "SO": 0, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 1},
    {"name": "U. Bermudez", "team": "LTU", "IP": "5.2", "H": 6, "R": 2, "ER": 2, "BB": 0, "SO": 3, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 49},
    {"name": "Y. Navas",    "team": "LTU", "IP": "4.1", "H": 8, "R": 4, "ER": 4, "BB": 1, "SO": 0, "HR": 1, "W": 0, "L": 1, "SV": 0, "pitches": 44},
]


def _try_import(schedule_id, home_runs, away_runs, home_hits, away_hits,
                home_errors, away_errors, wp, lp, sv, batting, pitching,
                home_linescore, away_linescore, label):
    try:
        gid = insert_game(
            schedule_id=schedule_id,
            home_runs=home_runs, away_runs=away_runs,
            home_hits=home_hits, away_hits=away_hits,
            home_errors=home_errors, away_errors=away_errors,
            wp=wp, lp=lp, sv=sv,
            batting=batting, pitching=pitching,
            home_linescore=home_linescore, away_linescore=away_linescore,
        )
        print(f"{label}: game_id={gid} OK")
    except ValueError as e:
        msg = str(e).encode("ascii", "replace").decode("ascii")
        if "expected >=" in msg and "outs" in msg:
            print(f"{label}: mercy/extra-inning IP warning (committed)")
        else:
            print(f"{label}: FAILED")
            print(msg)


def main() -> None:
    app = create_app()
    with app.app_context():
        _try_import(
            schedule_id=26,
            home_runs=0, away_runs=3,
            home_hits=7, away_hits=14,
            home_errors=1, away_errors=1,
            wp=("Y. Perez", "VCL"),
            lp=("Y. Panama", "SSP"),
            sv=None,
            batting=GAME26_BATTING, pitching=GAME26_PITCHING,
            home_linescore="0,0,0,0,0,0,0,0,0",
            away_linescore="0,0,2,0,0,0,1,0,0",
            label="Game 26 (VCL@SSP)",
        )
        _try_import(
            schedule_id=27,
            home_runs=2, away_runs=3,
            home_hits=8, away_hits=9,
            home_errors=1, away_errors=0,
            wp=("V. Baro", "CAV"),
            lp=("Y. Torres", "PRI"),
            sv=("E. Veliz", "CAV"),
            batting=GAME27_BATTING, pitching=GAME27_PITCHING,
            home_linescore="0,0,0,0,0,0,0,0,2",
            away_linescore="0,0,0,0,0,1,2,0,0",
            label="Game 27 (CAV@PRI)",
        )
        _try_import(
            schedule_id=28,
            home_runs=3, away_runs=6,
            home_hits=9, away_hits=14,
            home_errors=0, away_errors=1,
            wp=("A. Dela", "SCU"),
            lp=("Y. Navas", "LTU"),
            sv=None,
            batting=GAME28_BATTING, pitching=GAME28_PITCHING,
            home_linescore="0,0,1,1,0,0,1,0,0,0",
            away_linescore="0,0,0,0,0,2,0,1,0,3",
            label="Game 28 (SCU@LTU, 10 inn)",
        )


if __name__ == "__main__":
    main()
