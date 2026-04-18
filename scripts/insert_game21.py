"""Insert game 21: IND @ GRA, 15-6 in 10 innings. IND wins."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from services.game_import import insert_game

HOME = "GRA"
AWAY = "IND"

batting = [
    # IND (away)
    {"name": "J. Torriente", "team": AWAY, "AB": 6, "R": 2, "H": 3, "2B": 2, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "I. Chirino",   "team": AWAY, "AB": 6, "R": 2, "H": 3, "2B": 1, "3B": 0, "HR": 0, "RBI": 2, "BB": 0, "SO": 0},
    {"name": "R. Reyes",     "team": AWAY, "AB": 6, "R": 2, "H": 3, "2B": 0, "3B": 1, "HR": 0, "RBI": 2, "BB": 0, "SO": 1},
    {"name": "A. Malleta",   "team": AWAY, "AB": 6, "R": 2, "H": 3, "2B": 0, "3B": 0, "HR": 2, "RBI": 6, "BB": 0, "SO": 0},
    {"name": "Y. Urgelles",  "team": AWAY, "AB": 6, "R": 0, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "S. Hernandez", "team": AWAY, "AB": 5, "R": 3, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "Y. Amador",    "team": AWAY, "AB": 5, "R": 2, "H": 2, "2B": 0, "3B": 0, "HR": 2, "RBI": 4, "BB": 0, "SO": 0},
    {"name": "L. Correa",    "team": AWAY, "AB": 5, "R": 1, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "C. Tabares",   "team": AWAY, "AB": 4, "R": 1, "H": 1, "2B": 1, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 0},
    # GRA (home)
    {"name": "R. Videaux",   "team": HOME, "AB": 5, "R": 0, "H": 3, "2B": 0, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 0},
    {"name": "A. Despaigne", "team": HOME, "AB": 5, "R": 0, "H": 3, "2B": 1, "3B": 0, "HR": 0, "RBI": 2, "BB": 0, "SO": 1},
    {"name": "Y. Paumier",   "team": HOME, "AB": 5, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1},
    {"name": "Y. Cespedes",  "team": HOME, "AB": 5, "R": 1, "H": 1, "2B": 1, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2},
    {"name": "Y. Samon",     "team": HOME, "AB": 5, "R": 1, "H": 3, "2B": 1, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 2},
    {"name": "R. Tamayo",    "team": HOME, "AB": 5, "R": 1, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "M. Fonseca",   "team": HOME, "AB": 5, "R": 1, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0},
    {"name": "C. Benitez",   "team": HOME, "AB": 5, "R": 1, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 1},
    {"name": "L. Ferrales",  "team": HOME, "AB": 4, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2},
]

pitching = [
    # IND (away) pitchers
    {"name": "J. Garcia",   "team": AWAY, "IP": "3.2", "H": 12, "R": 6, "ER": 6, "BB": 0, "SO": 4, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 49},
    {"name": "F. Montieth", "team": AWAY, "IP": "5.1", "H": 4,  "R": 0, "ER": 0, "BB": 0, "SO": 5, "HR": 0, "W": 1, "L": 0, "SV": 0, "pitches": 49},
    {"name": "A. Rivero",   "team": AWAY, "IP": "1.0", "H": 1,  "R": 0, "ER": 0, "BB": 0, "SO": 0, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 6},
    # GRA (home) pitchers
    {"name": "M. Gonzalez", "team": HOME, "IP": "6.0", "H": 5,  "R": 3, "ER": 3, "BB": 0, "SO": 4, "HR": 1, "W": 0, "L": 0, "SV": 0, "pitches": 49},
    {"name": "L. Ramirez",  "team": HOME, "IP": "2.0", "H": 4,  "R": 1, "ER": 1, "BB": 0, "SO": 0, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 12},
    {"name": "A. Tamayo",   "team": HOME, "IP": "2.0", "H": 12, "R": 11,"ER": 11,"BB": 0, "SO": 0, "HR": 3, "W": 0, "L": 1, "SV": 0, "pitches": 26},
]

app = create_app()
with app.app_context():
    gid = insert_game(
        schedule_id=21,
        home_runs=6, away_runs=15,
        home_hits=17, away_hits=21,
        home_errors=0, away_errors=2,
        wp=("F. Montieth", AWAY),
        lp=("A. Tamayo", HOME),
        sv=None,
        batting=batting,
        pitching=pitching,
        home_linescore="0,4,1,1,0,0,0,0,0,0",
        away_linescore="0,0,0,1,0,2,1,0,2,9",
    )
    print(f"Inserted game_id={gid}")
