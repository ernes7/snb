"""Post-game tweets for games 26, 27, 28."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from services.weekly import save_game_tweets


GAME26_TWEETS = [
    # Panfilo (fav PRI, hate IND): nostalgic, pitcher-focused.
    # Perez CG shutout on 94 pitches — dream material for Panfilo.
    {
        "analyst_id": 1,
        "texto": "Yosbani Perez se trago al Sancti Spiritus: 9 innings, 7 ponches, blanqueada completa. Asi se pitcheaba antes. #ViejaEscuela",
        "replies": [
            {"commenter_id": 4, "texto": "Como Jose Antonio Huelga en el 71. Complete games, respeto al oficio."},
            {"commenter_id": 10, "texto": "El campesino no se cansa, como buen guajiro villaclareno. Bien por Perez."},
        ],
    },
    # Chequera (fav GRA, hate CAV): ALL CAPS, exaggerated.
    # Won't love a 3-0 pitcher's duel but will hype the shutout.
    {
        "analyst_id": 2,
        "texto": "3-0 EN EL LATINO??!! SIN JONRONES??!! ESTO NO ES BEISBOL, ESTO ES AJEDREZ CON BATES!! #DondeEstanLosBambinazos",
        "replies": [
            {"commenter_id": 2, "texto": "14 hits para VCL pero solo 3 carreras. OPS bajo, RISP terrible."},
            {"commenter_id": 9, "texto": "Chequera hasta para el ajedrez mete jonrones. Que personaje."},
        ],
    },
    # Facundo (fav SCU, hate LTU): formal, disciplined.
    # Will note Perez was pitching despite needing rest — the rule exception.
    {
        "analyst_id": 3,
        "texto": "Villa Clara sin abridores disponibles, forzado a usar a Perez bajo la regla de emergencia. Resultado: juego completo. Gestion de staff comprometida. #EstrategiaDesgastada",
        "replies": [
            {"commenter_id": 6, "texto": "Pitcheo de emergencia + complete game = doble castigo de descanso. Pagara la factura mas adelante."},
            {"commenter_id": 1, "texto": "Oye pero si el tipo sabe pitchar, dejalo. Asi era Contreras cuando no habia a quien mandar."},
        ],
    },
]


GAME27_TWEETS = [
    # Chequera (fav GRA, hate CAV): CAPS, HR-obsessed. CAV won with 2 HRs — he HATES this.
    {
        "analyst_id": 2,
        "texto": "ENRIQUEZ Y VEGA LE METIERON DOS VUELACERCAS A PINAR!! EL CIEGO DE AVILA NO PEGA NI CLAVOS PERO CUANDO PEGA, DUELE!! #RefuerzosDelCaribe",
        "replies": [
            {"commenter_id": 7, "texto": "Dos jonrones decisivos. Asi mismo es. Chequera no le gusta CAV pero tuvo que reconocer."},
            {"commenter_id": 8, "texto": "Profe, que es un vuelacerca? Mi papa dice que no es lo mismo que home run."},
            {"commenter_id": 6, "texto": "Carlitos, es sinonimo. Home run = vuelacerca = jonron = cuadrangular. Aprendete los cuatro."},
        ],
    },
    # Panfilo (fav PRI): DEVASTATED that PRI lost 3-2 with a 9th inning rally falling short.
    {
        "analyst_id": 1,
        "texto": "Pinar del Rio nunca se rinde: 2 carreras en el noveno para quedarse a una del empate. Rivera con su sacrificio, Leon con el triple. Dolor. #PinarHastaLaMuerte",
        "replies": [
            {"commenter_id": 5, "texto": "Panfilo, mi Pinar peleo hasta el final. No se puede pedir mas corazon. Proxima la ganamos."},
            {"commenter_id": 3, "texto": "Yo estaba viendo con mi esposo y casi me da un infarto cuando Rivera metio esa fly. Que emocion."},
            {"commenter_id": 10, "texto": "El que no arriesga no gana, pero el que no pega jonron tampoco. Asi es el beisbol."},
        ],
    },
    # Facundo (fav SCU): formal. Notes Miranda's 6 IP of scoreless relief+start, then Torres's collapse.
    {
        "analyst_id": 3,
        "texto": "Miranda Jr. lanzo 6 innings impecables, sin permitir carrera. Torres lo hereda y recibe dos cuadrangulares en 1.2 innings. Gestion de bullpen cuestionable. #TransicionFallida",
        "replies": [
            {"commenter_id": 6, "texto": "Cambio prematuro. Miranda solo llevaba 53 pitcheos, podia haber seguido."},
            {"commenter_id": 4, "texto": "En mis tiempos el abridor terminaba el juego. Nada de estas transiciones modernas."},
        ],
    },
]


GAME28_TWEETS = [
    # Chequera (fav GRA, hate CAV): CAPS. Hurtado went 3-for-5 with HR, 3 runs scored.
    {
        "analyst_id": 2,
        "texto": "RUSNEY HURTADO!! 3 HITS, 3 CARRERAS, UN JONRON EN SANTIAGO!! EL TIPO ES UNA MAQUINA DE HACER DANO!! #HurtadoMVP",
        "replies": [
            {"commenter_id": 7, "texto": "Santiago gano en extra innings y aun asi Chequera menciona al jugador contrario. El hombre es imparcial a veces."},
            {"commenter_id": 1, "texto": "Hurtado tremendo, pero lo que se llevo el juego fue el octavo turno de Santiago en el 10mo."},
        ],
    },
    # Panfilo (fav PRI, hate IND): loves pitcher stories. Dela earned it in long relief.
    {
        "analyst_id": 1,
        "texto": "Adalberto Dela tuvo que lanzar 4.2 innings en relevo contra Las Tunas para traerse la victoria. Asi se gana en extra innings. #TrabajoSucio",
        "replies": [
            {"commenter_id": 4, "texto": "Rescate largo de verdad. Como cuando Rolando Macias lanzaba entradas a montones sin quejarse."},
            {"commenter_id": 3, "texto": "Pobrecito, 39 lanzamientos despues de Yasmani. Debe estar agotado."},
        ],
    },
    # Facundo (fav SCU, hate LTU): perfect target — his team won against his hated LTU in extras.
    {
        "analyst_id": 3,
        "texto": "Santiago de Cuba vence a Las Tunas 6-3 en 10 innings. Rally decisivo en el decimo con Hurtado como protagonista. Quiala conecto jonron y se robo 3 bases pero Las Tunas cayo. #SuperioridadSantiaguera",
        "replies": [
            {"commenter_id": 7, "texto": "SANTIAGO, SANTIAGO, SANTIAGO!! Las Tunas estaba pidiendo el juego prestado."},
            {"commenter_id": 10, "texto": "Quiala solito con 3 hits, un jonron y 3 robos. Casi gana el solo. Pero el beisbol es en equipo."},
            {"commenter_id": 8, "texto": "Profe, como se roban 3 bases en un juego? Eso es mucho o poco?"},
        ],
    },
]


def main() -> None:
    app = create_app()
    with app.app_context():
        save_game_tweets(game_id=26, tweets=GAME26_TWEETS)
        save_game_tweets(game_id=27, tweets=GAME27_TWEETS)
        save_game_tweets(game_id=28, tweets=GAME28_TWEETS)
        print("Tweets saved for games 26, 27, 28.")


if __name__ == "__main__":
    main()
