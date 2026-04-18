"""Post-game tweets for game 21: IND 15, GRA 6 (10 innings)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from services.weekly import save_game_tweets

tweets = [
    {
        "analyst_id": 1,  # Panfilo — nostalgic, pitcher-focused, hates IND
        "texto": "Gonzalez tiro seis entradas de lujo y todo lo tiraron por la borda en la decima; asi se rompe el corazon de un fanatico. #BullpenesEnLlamas",
        "replies": [
            {"commenter_id": 3, "texto": "Mi nieto lloraba viendo el juego, yo tambien lloraba adentro."},
            {"commenter_id": 4, "texto": "En los 80 un abridor como Gonzalez no lo sacaban ni a patadas."},
        ],
    },
    {
        "analyst_id": 2,  # Chequera — ALL CAPS, power-obsessed, GRA favorite
        "texto": "MALLETA SEIS IMPULSADAS! AMADOR DOS CUADRANGULARES! PERO MI GRANMA SE CAYO EN LA DECIMA Y NO LO PUEDO CREER! #LaDecimaFatal",
        "replies": [
            {"commenter_id": 1, "texto": "Asere eso fue una masacre, nueve carreras en un inning."},
            {"commenter_id": 2, "texto": "Tamayo 49.50 de efectividad esta noche, el OPS de Malleta esta en la luna."},
            {"commenter_id": 9, "texto": "Me dijeron que en el barrio Granma nadie quiere hablar hoy."},
        ],
    },
    {
        "analyst_id": 3,  # Facundo — formal, methodical
        "texto": "Seis a seis tras nueve entradas, un desenlace decidido por la calidad del relevo; Industriales capitalizo con veintiun imparables. #DisciplinaYResultado",
        "replies": [
            {"commenter_id": 6, "texto": "Tecnicamente el juego se perdio cuando sacaron a Gonzalez sin dejarlo cerrar la septima."},
            {"commenter_id": 10, "texto": "Quien siembra bullpen cosecha derrotas, como dice mi abuelo en Villa Clara."},
        ],
    },
]

app = create_app()
with app.app_context():
    save_game_tweets(game_id=21, tweets=tweets)
    print("Tweets saved for game 21")
