"""Insert game 24: VCL @ LTU, LTU walks off 8-7 in 11 innings."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from services.game_import import insert_game

HOME = "LTU"
AWAY = "VCL"

batting = [
    # VCL (away)
    {"name": "R. Lunar",    "team": AWAY, "AB": 6, "R": 2, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "A. Zamora",   "team": AWAY, "AB": 5, "R": 0, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "Y. Garcia",   "team": AWAY, "AB": 6, "R": 2, "H": 2, "2B": 0, "3B": 0, "HR": 1, "RBI": 1, "BB": 0, "SO": 0},
    {"name": "A. Borrero",  "team": AWAY, "AB": 4, "R": 2, "H": 3, "2B": 1, "3B": 0, "HR": 1, "RBI": 3, "BB": 1, "SO": 0},
    {"name": "A. Pestano",  "team": AWAY, "AB": 5, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "Y. Vido",     "team": AWAY, "AB": 5, "R": 0, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 0},
    {"name": "Y. Canto",    "team": AWAY, "AB": 5, "R": 0, "H": 2, "2B": 1, "3B": 0, "HR": 0, "RBI": 2, "BB": 0, "SO": 0},
    {"name": "Y. Diaz",     "team": AWAY, "AB": 5, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "E. Paret",    "team": AWAY, "AB": 5, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    # LTU (home)
    {"name": "G. Duvergel", "team": HOME, "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 2},
    {"name": "J. Pedroso",  "team": HOME, "AB": 5, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 1},
    {"name": "Y. Scull",    "team": HOME, "AB": 5, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "A. Quiala",   "team": HOME, "AB": 5, "R": 1, "H": 1, "2B": 0, "3B": 1, "HR": 0, "RBI": 0, "BB": 0, "SO": 2},
    {"name": "D. Castro",   "team": HOME, "AB": 5, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "Y. Alarcon",  "team": HOME, "AB": 5, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 1},
    {"name": "O. Arias",    "team": HOME, "AB": 5, "R": 2, "H": 2, "2B": 0, "3B": 0, "HR": 2, "RBI": 3, "BB": 0, "SO": 1},
    {"name": "J. Johnson",  "team": HOME, "AB": 4, "R": 1, "H": 3, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "A. Guerrero", "team": HOME, "AB": 4, "R": 3, "H": 4, "2B": 0, "3B": 0, "HR": 1, "RBI": 2, "BB": 0, "SO": 0},
]

pitching = [
    # VCL (away)
    {"name": "J. Martinez", "team": AWAY, "IP": "4.2", "H": 2,  "R": 0, "ER": 0, "BB": 0, "SO": 6, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 49},
    {"name": "R. Carrillo", "team": AWAY, "IP": "3.1", "H": 7,  "R": 3, "ER": 3, "BB": 0, "SO": 0, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 29},
    {"name": "Y. Ulacia",   "team": AWAY, "IP": "2.0", "H": 5,  "R": 5, "ER": 5, "BB": 0, "SO": 3, "HR": 3, "W": 0, "L": 1, "SV": 0, "pitches": 37},
    # LTU (home)
    {"name": "D. Mejias",   "team": HOME, "IP": "5.2", "H": 15, "R": 7, "ER": 7, "BB": 0, "SO": 1, "HR": 2, "W": 0, "L": 0, "SV": 0, "pitches": 49},
    {"name": "E. Sanchez",  "team": HOME, "IP": "5.1", "H": 1,  "R": 0, "ER": 0, "BB": 1, "SO": 0, "HR": 0, "W": 1, "L": 0, "SV": 0, "pitches": 38},
]

app = create_app()
with app.app_context():
    gid = insert_game(
        schedule_id=24,
        home_runs=8, away_runs=7,
        home_hits=14, away_hits=16,
        home_errors=0, away_errors=1,
        wp=("E. Sanchez", HOME),
        lp=("Y. Ulacia", AWAY),
        sv=None,
        batting=batting,
        pitching=pitching,
        home_linescore="0,0,0,0,0,1,0,1,5,0,1",
        away_linescore="2,1,2,2,0,0,0,0,0,0,0",
    )
    print(f"Inserted game_id={gid}")
