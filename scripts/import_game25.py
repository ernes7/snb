"""Import game 25: GRA 11, IND 0 (mercy rule, 7 innings)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from services.game_import import insert_game


BATTING = [
    # IND (away)
    {"name": "J. Torriente",  "team": "IND", "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "I. Chirino",    "team": "IND", "AB": 3, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2, "SB": 0},
    {"name": "R. Reyes",      "team": "IND", "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "A. Malleta",    "team": "IND", "AB": 3, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "Y. Urgelles",   "team": "IND", "AB": 2, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "S. Hernandez",  "team": "IND", "AB": 2, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "Y. Amador",     "team": "IND", "AB": 2, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "L. Correa",     "team": "IND", "AB": 2, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "C. Tabares",    "team": "IND", "AB": 2, "R": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    # GRA (home)
    {"name": "R. Videaux",    "team": "GRA", "AB": 5, "R": 3, "H": 3, "2B": 0, "3B": 1, "HR": 0, "RBI": 2, "BB": 0, "SO": 1, "SB": 0},
    {"name": "A. Despaigne",  "team": "GRA", "AB": 4, "R": 2, "H": 2, "2B": 1, "3B": 0, "HR": 1, "RBI": 5, "BB": 1, "SO": 0, "SB": 0},
    {"name": "Y. Paumier",    "team": "GRA", "AB": 4, "R": 0, "H": 4, "2B": 0, "3B": 0, "HR": 0, "RBI": 2, "BB": 0, "SO": 0, "SB": 0},
    {"name": "Y. Cespedes",   "team": "GRA", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "Y. Samon",      "team": "GRA", "AB": 4, "R": 1, "H": 3, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 1, "SB": 0},
    {"name": "R. Tamayo",     "team": "GRA", "AB": 4, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "M. Fonseca",    "team": "GRA", "AB": 4, "R": 2, "H": 3, "2B": 1, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 0, "SB": 0},
    {"name": "C. Benitez",    "team": "GRA", "AB": 4, "R": 1, "H": 2, "2B": 0, "3B": 0, "HR": 0, "RBI": 1, "BB": 0, "SO": 0, "SB": 0},
    {"name": "L. Ferrales",   "team": "GRA", "AB": 2, "R": 1, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 1, "BB": 1, "SO": 0, "SB": 0},
]

PITCHING = [
    {"name": "J. Socarras", "team": "IND", "IP": "3.1", "H": 15, "R": 10, "ER": 9, "BB": 2, "SO": 1, "HR": 1, "W": 0, "L": 1, "SV": 0, "pitches": 52},
    {"name": "A. Rivero",   "team": "IND", "IP": "2.2", "H": 5,  "R": 1,  "ER": 1, "BB": 0, "SO": 1, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 27},
    {"name": "C. Licea",    "team": "GRA", "IP": "3.2", "H": 0,  "R": 0,  "ER": 0, "BB": 0, "SO": 5, "HR": 0, "W": 1, "L": 0, "SV": 0, "pitches": 29},
    {"name": "E. Blanco",   "team": "GRA", "IP": "3.1", "H": 1,  "R": 0,  "ER": 0, "BB": 0, "SO": 1, "HR": 0, "W": 0, "L": 0, "SV": 0, "pitches": 21},
]


def main() -> None:
    app = create_app()
    with app.app_context():
        try:
            game_id = insert_game(
                schedule_id=25,
                home_runs=11, away_runs=0,
                home_hits=20, away_hits=1,
                home_errors=1, away_errors=1,
                wp=("C. Licea", "GRA"),
                lp=("J. Socarras", "IND"),
                sv=None,
                batting=BATTING,
                pitching=PITCHING,
                home_linescore="2,2,6,0,0,1,0",
                away_linescore="0,0,0,0,0,0,0",
            )
            print(f"Game inserted: game_id={game_id}")
        except ValueError as e:
            msg = str(e).encode("ascii", "replace").decode("ascii")
            if "expected >=" in msg and "outs" in msg:
                print("Mercy-rule IP warning (data committed):")
                print(msg)
            else:
                raise


if __name__ == "__main__":
    main()
