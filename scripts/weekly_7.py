"""Week 7 weekly finalization: POTW, blurbs, analyses."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from db import get_db
from services.power_rankings import compute_power_rankings
from services.weekly import save_weekly_awards, save_weekly_tweets


BLURBS = {
    "GRA": "Tras una paliza 11-0 al Industriales con 20 imparables del equipo, y el grand-slam-mas de Alfredo Despaigne, los Alazanes suben a la cima del ranking. La rotacion (Licea y Blanco combinaron para 1 hit permitido) esta dominando.",
    "CAV": "Ciego pierde la cima pero no por falta de garra: 3-2 sobre Pinar con dos jonrones (Enriquez y Vega) y un rescate de 5.1 de Baro. Veliz cerro con ponche. Un equipo que gana juegos cerrados.",
    "SCU": "Santiago consigue un triunfo agotador 6-3 sobre Las Tunas en 10 entradas. Hurtado explota (3-5, HR, 3 carreras) y Dela sella 4.2 de relevo impecables. Bajan al #3 por margenes pequenos.",
    "PRI": "Pinar cae 3-2 en casa contra Ciego despues de un rally de dos carreras en el noveno que se quedo a uno. Miranda Jr. lanzo 6 entradas en blanco, pero Torres colapsa en el octavo con dos jonrones.",
    "VCL": "Villa Clara da la sorpresa de la semana: blanquea 3-0 al Sancti Spiritus con Yosvani Perez lanzando juego completo de 7 hits y 7 ponches. El resto: sin abridores disponibles, emergencia pura.",
    "SSP": "Sancti Spiritus blanqueado 0-3 en casa a pesar de 7 hits repartidos. Panama cargo con la derrota (2 ER en 5.1), y los bates se quedaron fríos cuando mas contaba. Semana para olvidar.",
    "LTU": "Las Tunas cae 3-6 ante Santiago en 10 entradas. Quiala hace lo imposible (3-4, HR, 3 bases robadas) pero el bullpen no aguanto: Navas permitio 4 carreras en 4.1 innings con dos jonrones.",
    "IND": "Industriales destruido 11-0 por Granma en regla de piedad. Socarras aporto un desastre (15 hits y 10 carreras en 3.1), y la ofensiva no produjo nada. Cayeron al ultimo lugar del ranking.",
}


WEEKLY_ANALYSES = [
    # Panfilo (fav PRI, hate IND) — nostalgic, pitcher-focused
    {
        "analyst_id": 1,
        "texto": "La semana siete nos regalo dos obras maestras desde el montículo que merecen quedarse en la memoria. Yosvani Perez se echo a Villa Clara al hombro con una blanqueada de nueve innings y siete ponches, recordandome aquellas tardes en que Huelga y Macias decidian sus juegos sin pedir ayuda. Del otro lado, Licea y Blanco se combinaron para permitir un solo hit al Industriales, lo cual deberia hacernos hablar menos de home runs y mas de brazos como estos. Pinar peleo hasta la ultima entrada contra Ciego, y aunque la derrota duele, un rally de dos carreras en el noveno demuestra que mi equipo nunca se rinde.",
    },
    # Chequera (fav GRA, hate CAV) — CAPS, power-obsessed
    {
        "analyst_id": 2,
        "texto": "GRANMA METIO 11 CARRERAS CON 20 HITS, DESPAIGNE PUSO UN JONRON CON 5 IMPULSADAS EN UN SOLO JUEGO!! ESO ES BEISBOL DE VERDAD!! Las Tunas y Santiago me regalaron otro partidazo con tres jonrones repartidos y un triunfo santiaguero en el 10mo, asi me gusta ver pegar la pelota! El Ciego de Avila gano con dos vuelacercas de Enriquez y Vega, lo unico que justifica su victoria, porque sin el bate largo no valen nada. Ya basta de 3-2 y 3-0, queremos 11-0 todas las semanas con jonrones a granel.",
    },
    # Facundo (fav SCU, hate LTU) — formal, disciplined, methodical
    {
        "analyst_id": 3,
        "texto": "La semana se caracterizo por dos juegos decididos por margen minimo y dos pichazos contundentes que alteraron las posiciones del campeonato. Santiago de Cuba impuso su superioridad fisica y mental sobre Las Tunas en diez innings, con una actuacion brillante de Hurtado y el relevo oportuno de Adalberto Dela. Villa Clara se vio forzado a utilizar a Yosvani Perez sin descanso reglamentario, una decision que le costara al staff mas adelante cuando el derecho tenga que cumplir ocho juegos acumulados de inactividad. Granma se afianzo en la pelea por el titulo con una demostracion ofensiva apabullante, mientras Industriales sigue buscando su identidad en el fondo de la tabla.",
    },
]


def main() -> None:
    app = create_app()
    with app.app_context():
        db = get_db()
        team_short = {row["id"]: row["short_name"]
                      for row in db.execute("SELECT id, short_name FROM teams").fetchall()}

        rankings = compute_power_rankings(7)
        for r in rankings:
            r["blurb"] = BLURBS[team_short[r["team_id"]]]

        save_weekly_awards(
            week_num=7,
            potw_player_id=98,  # R. Hurtado (SCU) — led his team to extra-inning win
            potw_summary="Rusney Hurtado fue el heroe del juego extendido: 3-5 con jonron, 3 carreras anotadas y 1 impulsada en la victoria 6-3 de Santiago sobre Las Tunas en 10 innings. En una semana donde el pitcheo domino, su aporte ofensivo resulto decisivo.",
            power_rankings=rankings,
            game_of_week_id=29,  # CAV @ GRA week 8 — top-of-table rematch
        )
        print("Weekly awards saved.")

        save_weekly_tweets(7, WEEKLY_ANALYSES)
        print("Weekly analyses saved.")


if __name__ == "__main__":
    main()
