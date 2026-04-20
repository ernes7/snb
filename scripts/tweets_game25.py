"""Post-game tweets for game 25: GRA 11, IND 0 (mercy rule)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from services.weekly import save_game_tweets


TWEETS = [
    # 1 - Panfilo (fav PRI, hate IND): nostalgic, suffering, pitcher-focused.
    # Loves to talk pitching — Licea + Blanco combined no-hitter (well, 1 hit) is his dream.
    {
        "analyst_id": 1,
        "texto": "Licea y Blanco casi lanzan juntos un sin hits al Industriales. Brillante actuacion del bullpen granmense. #BuenPitcheoGana",
        "replies": [
            {"commenter_id": 3, "texto": "Mi nieto dice que los Industriales estan descompuestos. Yo no entiendo de eso pero el marcador esta feo."},
            {"commenter_id": 6, "texto": "Tecnicamente no es no-hitter si dieron un hit. Pero la actuacion fue dominante, sin duda."},
        ],
    },
    # 2 - Chequera (fav GRA, hate CAV): ALL CAPS, exaggerated, power-obsessed.
    # GRA is his favorite — Despaigne's grand slam-ish HR will get him hyped.
    {
        "analyst_id": 2,
        "texto": "ALFREDO DESPAIGNE SACO UNA BOLA A LA CALLE Y METIO 5 CARRERAS EN UN SOLO JUEGO!! EL GRANMA ES UNA MAQUINA!! #DespaigneMonstruo",
        "replies": [
            {"commenter_id": 1, "texto": "Asere ese Despaigne esta en otro nivel, no hay pitcher que lo pare."},
            {"commenter_id": 2, "texto": "5 IMP en 4 VB con 1 BB. OPS del juego probablemente por encima de 2.500. #Numeros"},
            {"commenter_id": 7, "texto": "Bueno en Santiago no le damos tanto bombo pero el tipo pega duro, hay que reconocerlo."},
        ],
    },
    # 3 - Facundo (fav SCU, hate LTU): formal, disciplined, methodical.
    # Will analyze the mercy rule, Paumier 4-for-4 dry spell, and the 6-run third.
    {
        "analyst_id": 3,
        "texto": "Regla de piedad en el septimo. El tercer inning de 6 carreras definio el juego. Paumier de 4-4 sin anotar, curioso dato. #AnalisisBeisbol",
        "replies": [
            {"commenter_id": 4, "texto": "En mis tiempos jugabamos los 9 innings aunque perdieras 20-0. Ahora cualquiera se rinde temprano."},
            {"commenter_id": 10, "texto": "Como dice el guajiro: cuando la yegua corre, nadie la para. Granma esta desatado."},
        ],
    },
]


def main() -> None:
    app = create_app()
    with app.app_context():
        save_game_tweets(game_id=25, tweets=TWEETS)
        print("Tweets saved for game 25.")


if __name__ == "__main__":
    main()
