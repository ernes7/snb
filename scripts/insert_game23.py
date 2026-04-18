"""Insert game 23: CAV @ PRI, CAV wins 8-3."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from services.game_import import insert_game

HOME = "PRI"
AWAY = "CAV"

batting = [
    # CAV (away)
    {"name": "A. Sanchez",     "team": AWAY, "AB": 5, "R": 2, "H": 3, "2B": 1, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "M. Enriquez",    "team": AWAY, "AB": 5, "R": 2, "H": 2, "2B": 1, "3B": 0, "HR": 1, "RBI": 3, "BB": 0, "SO": 0},
    {"name": "Y. Charles",     "team": AWAY, "AB": 5, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 1, "RBI": 2, "BB": 0, "SO": 0},
    {"name": "Y. Fiss",        "team": AWAY, "AB": 5, "R": 1, "H": 1, "2B": 1, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 0},
    {"name": "I. Martinez",    "team": AWAY, "AB": 5, "R": 1, "H": 3, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "M. Vega",        "team": AWAY, "AB": 4, "R": 0, "H": 3, "2B": 1, "3B": 0, "HR": 0, "RBI": 2, "BB": 0, "SO": 0},
    {"name": "Y. Borroto",     "team": AWAY, "AB": 5, "R": 0, "H": 4, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "A. Civil",       "team": AWAY, "AB": 5, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "L. Diaz",        "team": AWAY, "AB": 5, "R": 1, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    # PRI (home)
    {"name": "Y. Cerce",       "team": HOME, "AB": 4, "R": 2, "H": 2, "2B": 0, "3B": 0, "HR": 1, "RBI": 1, "BB": 0, "SO": 1},
    {"name": "D. Duarte",      "team": HOME, "AB": 4, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 1, "RBI": 2, "BB": 0, "SO": 0},
    {"name": "O. Del Rosario", "team": HOME, "AB": 4, "R": 0, "H": 2, "2B": 0, "3B": 1, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "D. Castillo",    "team": HOME, "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "N. Concepcion",  "team": HOME, "AB": 4, "R": 0, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "Y. Peraza",      "team": HOME, "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2},
    {"name": "R. Leon",        "team": HOME, "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "M. Rivera",      "team": HOME, "AB": 3, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 1, "SO": 0},
    {"name": "L. Blanco",      "team": HOME, "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "O. Madera",      "team": HOME, "AB": 1, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
]

pitching = [
    # CAV (away)
    {"name": "V. Garcia",  "team": AWAY, "IP": "4.2", "H": 4, "R": 1, "ER": 1, "BB": 0, "SO": 4, "HR": 1, "W": 0, "L": 0, "SV": 0, "pitches": 49},
    {"name": "O. Carrero", "team": AWAY, "IP": "4.0", "H": 5, "R": 2, "ER": 2, "BB": 0, "SO": 3, "HR": 1, "W": 1, "L": 0, "SV": 0, "pitches": 49},
    {"name": "E. Veliz",   "team": AWAY, "IP": "0.1", "H": 0, "R": 0, "ER": 0, "BB": 1, "SO": 1, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 8},
    # PRI (home)
    {"name": "V. Banos",   "team": HOME, "IP": "8.1", "H": 18,"R": 8, "ER": 8, "BB": 0, "SO": 1, "HR": 2, "W": 0, "L": 1, "SV": 0, "pitches": 49},
    {"name": "J. Guerra",  "team": HOME, "IP": "0.2", "H": 1, "R": 0, "ER": 0, "BB": 0, "SO": 0, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 7},
]

app = create_app()
with app.app_context():
    gid = insert_game(
        schedule_id=23,
        home_runs=3, away_runs=8,
        home_hits=9, away_hits=19,
        home_errors=0, away_errors=0,
        wp=("O. Carrero", AWAY),
        lp=("V. Banos", HOME),
        sv=None,
        batting=batting,
        pitching=pitching,
        home_linescore="0,0,1,0,0,2,0,0,0",
        away_linescore="0,1,0,0,3,2,0,2,0",
    )
    print(f"Inserted game_id={gid}")
