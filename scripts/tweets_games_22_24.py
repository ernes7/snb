"""Post-game tweets for games 22, 23, 24."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from services.weekly import save_game_tweets

# Game 22: SSP 1, SCU 0 — Jimenez blanks SCU, Gourriel Jr solo HR the only run
tweets_22 = [
    {
        "analyst_id": 1,  # Panfilo — pitcher-focused, nostalgic
        "texto": "Jimenez y Socarras combinaron blanqueada, solo se necesito un jonron de Gourriel Jr para ganar; asi se juega a la antigua. #PelotaDeLaBuena",
        "replies": [
            {"commenter_id": 4, "texto": "En los 80 todos los juegos eran asi, nada de jonrones baratos."},
            {"commenter_id": 6, "texto": "Tecnicamente Jimenez poncho 3 en 6.2, eficiencia pura."},
        ],
    },
    {
        "analyst_id": 2,  # Chequera — ALL CAPS, power-obsessed
        "texto": "GOURRIEL JR SACO LA UNICA QUE HACIA FALTA! UN JONRON Y PA LA CASA! SSP GANA UNO A CERO Y YO QUERIA MAS CUADRANGULARES! #SoloUnoPeroBueno",
        "replies": [
            {"commenter_id": 1, "texto": "Asere eso fue un duelo de pitcheo, poca accion."},
            {"commenter_id": 2, "texto": "Vera con 2.46 PCL y aun asi perdio, el beisbol es cruel."},
        ],
    },
    {
        "analyst_id": 3,  # Facundo — formal
        "texto": "Encuentro decidido por una sola carrera temprana, con relevo perfecto de Socarras para preservar el uno cero; disciplina ejemplar. #PitcheoYControl",
        "replies": [
            {"commenter_id": 6, "texto": "El save de Socarras fue impecable, 2.1 sin permitir carrera."},
            {"commenter_id": 10, "texto": "Quien no aprovecha las bases llenas se queda con cero, como siempre digo."},
        ],
    },
]

# Game 23: CAV 8, PRI 3 — V. Banos pounded for 18 hits, CAV offense explodes
tweets_23 = [
    {
        "analyst_id": 1,  # Panfilo
        "texto": "V. Banos tragando dieciocho imparables en 8.1 entradas, eso no es pitchear eso es sobrevivir; Pinar necesita un relevo urgente. #RotacionEnCrisis",
        "replies": [
            {"commenter_id": 5, "texto": "Mayelin llorando, Banos sufrio demasiado hoy."},
            {"commenter_id": 2, "texto": "ERA de Banos subiendo como el precio del arroz."},
        ],
    },
    {
        "analyst_id": 2,  # Chequera
        "texto": "ENRIQUEZ Y CHARLES SACARON LA BOLA DEL PARQUE! BORROTO CUATRO INCOGIBLES! CIEGO DE AVILA DESATADO CON DIECINUEVE HITS! #OfensivaCiclonica",
        "replies": [
            {"commenter_id": 1, "texto": "Borroto 1.000 de average hoy, increible."},
            {"commenter_id": 7, "texto": "Cerce y Duarte sacaron jonrones pero no alcanzo."},
            {"commenter_id": 9, "texto": "En el barrio de Pinar estan quemando las gorras."},
        ],
    },
    {
        "analyst_id": 3,  # Facundo
        "texto": "Diecinueve imparables de Ciego de Avila sobre Banos reflejan falta de variacion en sus lanzamientos; la ofensiva explota cuando el pitcher repite. #LecturaDelJuego",
        "replies": [
            {"commenter_id": 6, "texto": "Banos necesita trabajar en su secuencia de lanzamientos."},
            {"commenter_id": 10, "texto": "Quien no cambia de ritmo no gana, como el guaguanco."},
        ],
    },
]

# Game 24: LTU 8, VCL 7 in 11 innings — Guerrero 4-for-4, Arias 2 HR, LTU walk-off
tweets_24 = [
    {
        "analyst_id": 1,  # Panfilo — hates LTU (favorite PRI)
        "texto": "Once entradas para que Las Tunas saque un milagro con jonrones de Arias y Guerrero; el bullpen de Villa Clara se derrumbo como siempre. #RelevosSinAlma",
        "replies": [
            {"commenter_id": 3, "texto": "Mi nieto aguanto hasta las once entradas, yo no pude."},
            {"commenter_id": 4, "texto": "En los 80 Ulacia no vuelve a lanzar en un mes despues de esa actuacion."},
        ],
    },
    {
        "analyst_id": 2,  # Chequera
        "texto": "ARIAS DOS CUADRANGULARES! GUERRERO CUATRO HITS Y UN BAMBINAZO! VILLA CLARA CON DIECISEIS HITS Y PIERDE EN LA ONCE, QUE DOLOR! #ExtrainningAsesinos",
        "replies": [
            {"commenter_id": 1, "texto": "Guerrero 4 de 4, bateo perfecto mi hermano."},
            {"commenter_id": 2, "texto": "Ulacia ERA de 22.50 esta noche, desastre total."},
            {"commenter_id": 8, "texto": "Profe explicame como pierdes con 16 hits???"},
        ],
    },
    {
        "analyst_id": 3,  # Facundo — hates LTU
        "texto": "Partido extenso decidido por la profundidad del bullpen tunero; E. Sanchez con 5.1 entradas de relevo sin carrera definio el desenlace. #FortalezaEnElRelevo",
        "replies": [
            {"commenter_id": 6, "texto": "Sanchez poncho 0 pero no permitio carreras, eso es control."},
            {"commenter_id": 10, "texto": "Quien pitchea hasta el final se come la victoria, como la tierra al guajiro."},
        ],
    },
]

app = create_app()
with app.app_context():
    save_game_tweets(game_id=22, tweets=tweets_22)
    print("Game 22 tweets saved")
    save_game_tweets(game_id=23, tweets=tweets_23)
    print("Game 23 tweets saved")
    save_game_tweets(game_id=24, tweets=tweets_24)
    print("Game 24 tweets saved")
