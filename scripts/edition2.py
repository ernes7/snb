"""Edition 2 of En Tres y Dos — covers weeks 5-8."""
from app import create_app
from blueprints.periodico.services import save_edition

HEADLINE = "Cuatro Equipos Empatados en la Cima: La Liga Se Niega a Tener Dueno"
SUBHEADLINE = (
    "Amador mete tres jonrones en un juego, Chirino batea .583 sin vuelacercas, "
    "y Sancti Spiritus vive de cuadrangulares con 29 en la temporada"
)

ARTICLES = [
    # ── [0] El Panorama (lead) ──
    {
        "type": "feature",
        "title": "El Empate Mas Apretado en la Historia del Torneo",
        "subtitle": (
            "Cuatro equipos comparten 5-3 en la cima, nadie se separa "
            "y el ranking de poder no alcanza para decidir"
        ),
        "body": (
            "<p>Ocho semanas de pelota y la tabla de posiciones parece un juego de domino "
            "donde nadie puede poner la ficha ganadora. Ciego de Avila, Santiago de Cuba, "
            "Pinar del Rio y Granma comparten record de 5-3, separados unicamente por "
            "decimales en un ranking de poder que cambia de lider cada semana. Esto no es "
            "una carrera: es un nudo.</p>"

            "<p>El ranking le da la ventaja tecnica a Ciego de Avila (0.836), impulsado por "
            "un diferencial de carreras solido y el unico invicto contra Pinar (2-0), ganando "
            "juegos apretados 8-3 y 3-2 donde el bullpen de los Tigres cerro la puerta. "
            "Santiago se sostiene segundo con la segunda mejor ofensiva de la liga (.322) y el "
            "bat de Bell, que lidera las impulsadas con 12. Granma ocupa el tercero con el "
            "mejor average colectivo (.324), pero dos derrotas escandalosas por paliza les "
            "pesan en el diferencial. Pinar cierra el cuarteto con la mejor efectividad "
            "colectiva del torneo (3.13), pero sus dos caidas ante Ciego los ponen en "
            "desventaja directa.</p>"

            "<p>Debajo de la linea de clasificacion, Industriales y Sancti Spiritus a 3-5 "
            "todavia respiran, pero una racha de dos derrotas mas los entierra. Las Tunas con "
            "su 8.49 de efectividad colectiva es el saco de boxeo de la liga: tres juegos de "
            "misericordia recibidos y contando. Villa Clara a 2-6 es un caso clinico "
            "— sus unicas victorias fueron contra Sancti Spiritus, y van 0-6 contra todos "
            "los demas. El fondo de la tabla es tan claro como la cima es caotica.</p>"

            "<p>Las proximas cuatro semanas definiran todo. Los enfrentamientos directos entre "
            "los cuatro lideres romperan empates. La pregunta no es quien es mejor — nadie "
            "lo es. La pregunta es quien parpadea primero.</p>"
        ),
        "author": None,
        "stat_callout": {
            "value": "5-3",
            "label": "record compartido por CAV, SCU, PRI y GRA en la cima",
        },
    },

    # ── [1] La Nota del Dia — Amador ──
    {
        "type": "feature",
        "title": "Tres Jonrones en Un Juego: Amador Explota Contra Las Tunas",
        "subtitle": (
            "El toletero de Industriales puso tres vuelacercas en la Semana 8 "
            "y se convirtio en el nombre mas caliente de la liga"
        ),
        "body": (
            "<p>Y. Amador era un bateador de banca. Una pieza de recambio para noches "
            "de descanso y emergencias. Ocho semanas despues tiene cinco jonrones, ocho "
            "impulsadas, .400 de average, y la actuacion individual mas explosiva de la "
            "temporada: tres cuadrangulares en un solo juego contra Las Tunas, sepultando "
            "a los lenaderos 10-0 en juego de misericordia.</p>"

            "<p>El juego de tres jonrones es materia de leyenda en la pelota cubana. El "
            "primero fue un slider que se quedo arriba y Amador lo castigo a la banda "
            "contraria. El segundo, una recta adentro que jalo con todo el cuerpo. El "
            "tercero ni necesito explicacion — contacto limpio, sonido seco, bola que "
            "desaparece. El estadio ya sabia antes de mirar. Su actuacion le valio el "
            "premio de Jugador de la Semana y lo puso en la conversacion del Kindelan.</p>"

            "<p>Industriales necesitaba esto. A 3-5, la temporada se les escapaba hacia "
            "la irrelevancia. La explosion de Amador, sumada a la consistencia de Malleta "
            "(6 jonrones en la campana, Jugador de la Semana en la sexta), le da a los "
            "azules el tandem de poder mas peligroso de la liga desde la banca hasta el "
            "lineup titular. Si ambos siguen conectando, Industriales tiene ofensiva para "
            "competir. Pero el pitcheo (5.04 de efectividad) sigue siendo la grieta en "
            "la represa.</p>"

            "<p>Lo que hace el juego de Amador aun mas notable es el contexto. Las Tunas ya "
            "estaba muerto — 8.49 de efectividad, tres juegos de misericordia en contra. "
            "Pero tres vuelacercas en cualquier juego, contra cualquier rival, es historico. "
            "El hombre paso de banca a titular de las paginas deportivas en cuatro "
            "semanas.</p>"
        ),
        "author": None,
        "stat_callout": {
            "value": "3",
            "label": "jonrones de Amador en un solo juego (Semana 8 vs LTU)",
        },
    },

    # ── [2] Radar Estadistico — Chirino ──
    {
        "type": "stats",
        "title": "Chirino a .583: El Mejor Bateador de la Liga No Puede Sacarla del Parque",
        "subtitle": (
            "El jardinero de Industriales sigue en la cima del average "
            "y sigue sin pegar un cuadrangular"
        ),
        "body": (
            "<p>En la primera edicion de En Tres y Dos senalamos la anomalia: Chirino "
            "bateaba .529 con cero impulsadas. Cuatro semanas despues, la anomalia crecio "
            "hasta convertirse en fenomeno estadistico. Chirino lidera la liga con .583 "
            "de average — mas de 150 puntos por encima de Videaux, el segundo (.429). "
            "Tiene 21 hits en 36 turnos. Y no ha conectado un solo cuadrangular.</p>"

            "<p>En una liga donde Sancti Spiritus tiene 29 jonrones como equipo y un bateador "
            "de banca como Amador mete tres en un juego, Chirino es puro arte del contacto "
            "sin un solo signo de exclamacion. Se embasa a un ritmo absurdo, pero sin poder "
            "de extra bases, su produccion depende enteramente de lo que venga detras en el "
            "lineup. Es el mejor bateador del que nadie habla — el maestro silencioso en una "
            "liga que solo escucha el estruendo del batazo largo.</p>"
        ),
        "author": None,
        "stat_callout": {
            "value": ".583",
            "label": "AVG de Chirino con 0 jonrones en toda la temporada",
        },
    },

    # ── [3] Radar Estadistico — SSP power ──
    {
        "type": "stats",
        "title": "Sancti Spiritus: 29 Jonrones y Record Perdedor",
        "subtitle": (
            "Los espirituanos viven y mueren por el batazo largo "
            "— nada entre el palo y la nada"
        ),
        "body": (
            "<p>Sancti Spiritus ha conectado 29 cuadrangulares, mas que cualquier equipo en "
            "el torneo. Tambien batea .290 colectivo, cuarto entre ocho equipos. Esta es una "
            "ofensiva que opera en binario: o la bola sale del parque o no pasa nada. No hay "
            "small ball aqui, no hay carreras manufacturadas, no hay muerte por mil sencillos. "
            "Todo o nada.</p>"

            "<p>El problema es que estan 3-5. Cuando el cuadrangular no aparece, la ofensiva "
            "se muere. Cepeda (5 HR) es el ancla, L. Gourriel Jr. y E. Sanchez (4 cada uno) "
            "completan el nucleo de poder, y Jimenez desde la loma (0.00 de efectividad, 38 "
            "outs registrados) es el mejor lanzador de la liga por cualquier metrica. Pero ni "
            "la perfeccion de Jimenez puede salvar una ofensiva que se olvida de anotar cuando "
            "no puede volarla por encima de la cerca. Sancti Spiritus es un equipo de extremos "
            "— pitcheo brillante, ofensiva de fiesta o hambruna, y un record que refleja "
            "ese caos.</p>"
        ),
        "author": None,
        "stat_callout": {
            "value": "29",
            "label": "HR de Sancti Spiritus, lider de liga, con .290 de average y record de 3-5",
        },
    },

    # ── [4] Radar Estadistico — stolen base drought ──
    {
        "type": "stats",
        "title": "Cuatro Bases Robadas en Ocho Semanas: La Liga Que No Corre",
        "subtitle": "El robo de base desaparecio del torneo y nadie parece notarlo",
        "body": (
            "<p>En 32 juegos disputados esta temporada, con ocho equipos y cientos de turnos "
            "al bate, se han robado exactamente cuatro bases. Cuatro. Eso es un robo cada "
            "ocho juegos. En una liga con corredores como Tabares, Olivera y Zamora — todos "
            "calificados entre los mas rapidos de sus planteles — nadie esta corriendo.</p>"

            "<p>La muerte del robo de base refleja un cambio de filosofia: para que arriesgar "
            "un out en las bases cuando los jonrones caen a ritmo record? Con cinco juegos de "
            "misericordia y equipos lanzando bombas a voluntad, el calculo dice quedate quieto "
            "y espera por el cuadrangular de tres carreras. La pelota cubana siempre celebro "
            "la velocidad y la audacia en los caminos. Este torneo mato esa tradicion y la "
            "reemplazo con el batazo largo. Si eso es evolucion o involucion depende de a "
            "cual generacion de fanatico le preguntes.</p>"
        ),
        "author": None,
        "stat_callout": {
            "value": "4",
            "label": "bases robadas en 32 juegos del torneo",
        },
    },

    # ── [5] La Carrera ──
    {
        "type": "column",
        "title": "La Carrera: Tres Lanzadores Perfectos y Un Bateador Invisible",
        "subtitle": (
            "Jimenez, Miranda Jr. y Mora sostienen 0.00 de efectividad "
            "— mientras Chirino domina el Kindelan sin un solo batazo largo"
        ),
        "body": (
            "<p>El Premio Kindelan tiene tres candidatos fuertes separados por matices. "
            "Bell (.389, 4 HR, 12 RBI) lidera en impulsadas y su combinacion de poder con "
            "contacto lo coloca al frente. Amador (.400, 5 HR, 8 RBI) tiene el momento "
            "mas caliente de la liga y el multiplicador de actuaciones memorables. Despaigne "
            "(.406, 2 HR, 10 RBI) tiene el average mas alto del trio y el impulso del "
            "multiplicador de equipo si Granma se mantiene arriba. Chirino (.583) lidera "
            "el average crudo, pero sin poder de extra bases su OPS sufre y el premio castiga "
            "la falta de produccion de largo alcance. Hurtado (.424) y Videaux (.429) son los "
            "caballos oscuros: si mantienen esos promedios y suman impulsadas, pueden meterse "
            "en la pelea. Con 16 juegos restantes, el efecto multiplicador de la posicion en "
            "tabla puede reordenar todo.</p>"

            "<p>El Premio Lazo tiene una pregunta definida: quien rompe primero? Tres lanzadores "
            "mantienen efectividad perfecta de 0.00 — Jimenez (SSP, 38 outs, 7 SO), Miranda Jr. "
            "(PRI, 37 outs, 10 SO) y Mora (CAV, 25 outs, 11 SO). Jimenez tiene la ventaja en "
            "entradas pero su equipo esta 3-5, lo que reduce su multiplicador. Miranda Jr. "
            "combina volumen con ponches y su Pinar esta 5-3 — el perfil mas completo. Mora "
            "tiene menos entradas pero el ratio de ponches mas impresionante y un equipo "
            "puntero. Detras de ellos, V. Garcia (CAV, 1.00 ERA) y Bermudez (LTU, 1.42) "
            "son excelentes pero no perfectos.</p>"

            "<p>En la primera edicion predijimos que el club de ERA 0.00 se reduciria. Se "
            "redujo de cinco a tres, y los que sobrevivieron son los reales. La carrera del "
            "Lazo puede definirse en las proximas semanas cuando estos brazos enfrenten a las "
            "mejores ofensivas (Granma .324, Santiago .322). Si Miranda Jr. sobrevive lanzando "
            "contra esos lineups, el premio es suyo hasta que alguien se lo quite.</p>"
        ),
        "author": None,
        "stat_callout": None,
    },

    # ── [6] Retrovisores ──
    {
        "type": "callback",
        "title": "Retrovisores: Lo Que Dijeron y Lo Que Paso",
        "subtitle": None,
        "body": (
            "<p><strong>Chequera, Semana 5:</strong> \"VEGAAAA DOS JONRONES Y SEIS "
            "IMPULSADAS EN UN SOLO JUEGO!!!\" — Chequera estaba euforia pura celebrando "
            "a Vega de Ciego de Avila, el Jugador de la Semana. La ironia: Chequera detesta "
            "a los Tigres. Pero cuando el poder habla, el hombre no puede contenerse. "
            "El batazo es mas fuerte que la rivalidad. <em>Veredicto: envejecio de manera "
            "hilarante — Chequera elogiando al enemigo porque los batazos eran demasiado "
            "hermosos para negar.</em></p>"

            "<p><strong>Panfilo, Semana 5:</strong> Pinar gano 5-4 contra Industriales y "
            "Panfilo, en lugar de celebrar, se la paso preocupado por los margenes. El "
            "viejo olia sangre antes que nadie. Pinar despues perdio ambos juegos contra "
            "Ciego (8-3 y 3-2). La paranoia de Panfilo era profetica — su equipo ganaba "
            "feo y eventualmente la suerte se acabo contra un rival de verdad. "
            "<em>Veredicto: envejecio perfecto. El viejo huele las cosas antes de que "
            "pasen.</em></p>"

            "<p><strong>Facundo, Semanas 5-8:</strong> El profesor paso todo el bloque "
            "analizando fragilidad estructural y prediciendo que los equipos con planteles "
            "cortos colapsarian. Villa Clara (2-6) y Las Tunas (8.49 de efectividad) hicieron "
            "exactamente eso. Su analisis clinico de que Villa Clara estaba sobreexigiendo a "
            "sus lanzadores resulto certero — son el peor equipo de la liga. "
            "<em>Veredicto: envejecio perfecto. El profesor se saca A.</em></p>"

            "<p><strong>Chequera, Semana 8:</strong> \"CINCO JONRONES EN UN JUEGO!! AMADOR "
            "CON TRES Y MALLETA CON...\" — Chequera no podia contenerse viendo a Amador y "
            "Malleta destruir a Las Tunas. El hombre estaba euforico viendo poder de "
            "Industriales — un equipo con el que no tiene afiliacion alguna — porque las "
            "bolas estaban saliendo del parque. Su obsesion con el poder supera cualquier "
            "lealtad de camiseta. <em>Veredicto: puro Chequera — si sale del parque, lo "
            "ama sin importar el color del uniforme.</em></p>"
        ),
        "author": None,
        "stat_callout": None,
    },
]

INTERVIEW = {
    "analyst_id": 2,
    "player_id": 155,
    "title": (
        'Chequera entrevista a Y. Amador: '
        '"TRES VUELACERCAS EN UN JUEGO, HERMANO, ESO ES DE OTRO PLANETA"'
    ),
    "photo": "players/IND/Y_Amador.png",
    "questions": [
        {
            "q": (
                "Amador, TRES JONRONES CONTRA LAS TUNAS. Tres. En un solo juego. "
                "Dimelo en tus palabras, que sentiste cuando la tercera salio del parque?"
            ),
            "a": (
                "Mira Chequera, yo sabia que estaba viendo la bola bien desde el primer "
                "turno. La primera fue un slider que se quedo arriba, la segunda una recta "
                "que busco adentro y yo la jale, y la tercera... esa ni la vi salir, senti "
                "el contacto y el sonido y ya sabia. El estadio se vino abajo. Uno no "
                "planifica eso, simplemente te llega el dia."
            ),
        },
        {
            "q": (
                "Tu empezaste en la banca, NADIE hablaba de ti en la semana uno. Ahora "
                "tienes cinco jonrones, .400 de average, y eres el Jugador de la Semana. "
                "Que cambio?"
            ),
            "a": (
                "La oportunidad, Chequera. Cuando me pusieron a jugar regular, yo me dije: "
                "esto no me lo quita nadie. Cada turno es un examen y yo voy a aprobar. El "
                "primer jonron me dio confianza, el segundo me dio hambre, y ahora mismo no "
                "hay pitcher que me meta miedo. Estoy en la mejor racha de mi vida."
            ),
        },
        {
            "q": (
                "Yo respeto al que le pega duro a la bola. Tu y Malleta juntos tienen "
                "ONCE JONRONES entre los dos. Industriales esta produciendo mas poder "
                "desde la banca que muchos equipos desde el lineup titular. Como se "
                "explica eso?"
            ),
            "a": (
                "Malleta es un animal, ese tipo nacio para pegar jonrones. Cuando el "
                "conecta y yo vengo detras, o al reves, el pitcher no tiene respiro. "
                "Somos dos bateadores de poder que se complementan. El equipo se "
                "alimenta de eso, los demas ven que la bola sale del parque y se relajan, "
                "le pegan con mas confianza. El poder es contagioso."
            ),
        },
        {
            "q": (
                "Pero hermano, CINCO JONRONES TUYOS y el equipo esta 3-5. Con esa "
                "produccion deberian estar arriba. Que esta fallando?"
            ),
            "a": (
                "El pitcheo, Chequera. No te voy a mentir. Nosotros anotamos carreras, "
                "pero tambien permitimos muchas. Cuando tu efectividad esta por encima de "
                "cinco, necesitas pegar seis carreras cada noche para ganar, y eso no es "
                "sostenible. El brazo tiene que ayudar al bate. Pero yo creo en este "
                "equipo — si el pitcheo se estabiliza, tenemos ofensiva para competir "
                "con cualquiera."
            ),
        },
        {
            "q": (
                "Ultima pregunta y esta es de Chequera: si pudieras enfrentar a un "
                "lanzador, SOLO UNO, para demostrar que tu poder es real contra la "
                "elite... a quien le pegas?"
            ),
            "a": (
                "A Mora de Ciego. Cero carreras limpias en todo el torneo, dicen que es "
                "intocable. Bueno, yo quiero ser el que le rompa ese cero con un batazo "
                "que salga del estadio y caiga en la calle. Ponme contra el zurdo ese y "
                "vamos a ver si su cero sobrevive."
            ),
        },
    ],
}

app = create_app()
with app.app_context():
    save_edition(
        edition_num=2,
        week_num=8,
        headline=HEADLINE,
        subheadline=SUBHEADLINE,
        articles=ARTICLES,
        interview=INTERVIEW,
    )
    print("Edition 2 saved.")
