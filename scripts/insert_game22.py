"""Insert game 22: SCU @ SSP, 0-1. SSP shutout win."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from services.game_import import insert_game

HOME = "SSP"
AWAY = "SCU"

batting = [
    # SCU (away)
    {"name": "H. Olivera",     "team": AWAY, "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "R. Hurtado",     "team": AWAY, "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "A. Bell",        "team": AWAY, "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "J. Abreu",       "team": AWAY, "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2},
    {"name": "R. Merino",      "team": AWAY, "AB": 3, "R": 0, "H": 2, "2B": 0, "3B": 1, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "P. Poll",        "team": AWAY, "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "L. Nava",        "team": AWAY, "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "R. Orta",        "team": AWAY, "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "M. Castellanos", "team": AWAY, "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    # SSP (home)
    {"name": "F. Cepeda",      "team": HOME, "AB": 4, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2},
    {"name": "Y. Mendoza",     "team": HOME, "AB": 3, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "Y. Ibanez",      "team": HOME, "AB": 3, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "D. Moreira",     "team": HOME, "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "Y. Gourriel",    "team": HOME, "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "L. Gourriel Jr", "team": HOME, "AB": 3, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 1, "RBI": 1, "BB": 0, "SO": 1},
    {"name": "E. Sanchez",     "team": HOME, "AB": 3, "R": 0, "H": 1, "2B": 1, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2},
    {"name": "Y. Gourriel CF", "team": HOME, "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2},
    {"name": "Y. Bello",       "team": HOME, "AB": 2, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 1, "SO": 0},
]

pitching = [
    # SCU (away)
    {"name": "N. Vera",       "team": AWAY, "IP": "3.2", "H": 2, "R": 1, "ER": 1, "BB": 0, "SO": 7, "HR": 1, "W": 0, "L": 1, "SV": 0, "pitches": 49},
    {"name": "D. Betancourt", "team": AWAY, "IP": "4.1", "H": 2, "R": 0, "ER": 0, "BB": 1, "SO": 2, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 42},
    # SSP (home)
    {"name": "I. Jimenez",    "team": HOME, "IP": "6.2", "H": 1, "R": 0, "ER": 0, "BB": 0, "SO": 4, "HR": 0, "W": 1, "L": 0, "SV": 0, "pitches": 49},
    {"name": "Y. Socarras",   "team": HOME, "IP": "2.1", "H": 1, "R": 0, "ER": 0, "BB": 0, "SO": 1, "HR": 0, "W": 0, "L": 0, "SV": 1, "pitches": 12},
]

app = create_app()
with app.app_context():
    gid = insert_game(
        schedule_id=22,
        home_runs=1, away_runs=0,
        home_hits=4, away_hits=2,
        home_errors=0, away_errors=0,
        wp=("I. Jimenez", HOME),
        lp=("N. Vera", AWAY),
        sv=("Y. Socarras", HOME),
        batting=batting,
        pitching=pitching,
        home_linescore="0,1,0,0,0,0,0,0",
        away_linescore="0,0,0,0,0,0,0,0,0",
    )
    print(f"Inserted game_id={gid}")
