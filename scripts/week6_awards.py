"""Week 6 awards: POTW, power rankings blurbs, GOTW, weekly analyses."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from db import get_db
from services.power_rankings import compute_power_rankings
from services.weekly import save_weekly_awards, save_weekly_tweets


BLURBS = {
    "CAV": "Diecinueve imparables y tres jonrones en Pinar del Rio; Enriquez y Charles desataron la ofensiva mientras Borroto bateo de cuatro-cuatro. El bullpen preservo la ventaja sin sustos.",
    "SCU": "Vera lucio con siete ponches y 2.46 PCL pero el unico jonron de Gourriel Jr le costo el juego. Dos imparables no bastan ni con ese pitcheo.",
    "GRA": "Gonzalez tiro seis entradas solidas pero Tamayo hizo implosion en la decima con once carreras limpias. Malleta y Amador jonronearon y aun asi el bullpen se llevo el colapso.",
    "PRI": "Banos se comio dieciocho hits en 8.1 entradas y la ofensiva solo respondio con tres carreras. Cerce y Duarte jonronearon pero fue una noche para olvidar en el Capitan San Luis.",
    "SSP": "Blanqueada combinada de Jimenez y Socarras; el jonron solitario de L. Gourriel Jr fue toda la ofensiva que necesito el Sancti Spiritus. Pelota de manual.",
    "IND": "Garcia duro poco pero Montieth salvo con 5.1 entradas sin carrera y la ofensiva exploto con nueve carreras en la decima. Malleta impulso seis y Amador se voló dos.",
    "LTU": "Arias pego dos jonrones, Guerrero bateo de cuatro-cuatro con bambinazo y E. Sanchez tiro 5.1 entradas de relevo perfecto. Walk-off en la once para robarle el juego a Villa Clara.",
    "VCL": "Dieciseis imparables y aun asi perder en la once entrada; Ulacia regalo tres jonrones en dos capitulos para desperdiciar una joya de Martinez. Derrota dolorosa.",
}

WEEKLY_ANALYSES = [
    {
        "analyst_id": 1,  # Panfilo
        "texto": (
            "La semana seis trajo dos juegos decididos en entradas extras y un tema recurrente: "
            "los bullpenes se caen cuando mas se les necesita. Tamayo permitio once carreras limpias "
            "para regalar un juego de Granma y Ulacia tiro tres jonrones en dos entradas para hundir a Villa Clara. "
            "Mientras tanto, pitcheo de calidad como Jimenez de SSP o Montieth con sus 5.1 blanqueadas nos recordo como se gana a la antigua."
        ),
    },
    {
        "analyst_id": 2,  # Chequera
        "texto": (
            "QUE SEMANA DE JONRONES! MALLETA DOS, AMADOR DOS, ARIAS DOS, GUERRERO UNO, ENRIQUEZ, CHARLES, GOURRIEL JR, GARCIA, BORRERO, CERCE Y DUARTE! "
            "Industriales y Ciego de Avila desataron ofensivas historicas con quince y ocho carreras respectivamente. "
            "Mi Granma sufrio la peor derrota del torneo cuando el bullpen se rompio en la decima, UNA DESGRACIA. "
            "Y mientras tanto, Jimenez le tira una joya a los santiagueros para un uno a cero que nadie espero."
        ),
    },
    {
        "analyst_id": 3,  # Facundo
        "texto": (
            "La semana seis expuso la fragilidad estructural de ciertos bullpenes del torneo. "
            "Ciego de Avila escalo al primer puesto del ranking gracias a una ofensiva quirurgica contra Banos, mientras Pinar del Rio cayo cuatro posiciones. "
            "Sancti Spiritus e Industriales subieron con pitcheo de rotacion confiable y ofensiva oportuna. "
            "La profundidad del staff definira las proximas semanas mientras las series se acumulan y la fatiga pesa."
        ),
    },
]


def main() -> None:
    app = create_app()
    with app.app_context():
        rankings = compute_power_rankings(6)
        db = get_db()
        tid_to_short = {
            row["id"]: row["short_name"]
            for row in db.execute("SELECT id, short_name FROM teams").fetchall()
        }
        for r in rankings:
            r["blurb"] = BLURBS[tid_to_short[r["team_id"]]]
        save_weekly_awards(
            week_num=6,
            potw_player_id=148,  # A. Malleta — 3/6, 2 HR, 6 RBI in IND's 15-6 win
            potw_summary=(
                "A. Malleta ofrecio el rendimiento ofensivo mas contundente de la semana: "
                "3 de 6 con dos cuadrangulares y seis impulsadas en la vapuleada 15-6 sobre Granma. "
                "Su produccion fue el motor de la explosion industrialista en la decima entrada."
            ),
            power_rankings=rankings,
            game_of_week_id=24,  # VCL @ LTU 11-inning walk-off thriller
        )
        print("Week 6 awards saved")

        save_weekly_tweets(6, WEEKLY_ANALYSES)
        print("Week 6 analyses saved")


if __name__ == "__main__":
    main()
