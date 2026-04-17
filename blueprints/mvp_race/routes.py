"""MVP race blueprint routes."""
from __future__ import annotations

from flask import render_template
from markupsafe import Markup

from . import mvp_race_bp
from .awards import (
    compute_artesano_race,
    compute_clutch_race,
    compute_five_tools_race,
    compute_undercover_race,
    league_avg_overall,
)
from .services import compute_kindelan_race, compute_lazo_race


@mvp_race_bp.route('/mvp-race')
def mvp_race() -> str:
    """Six awards, each with its own scoring mechanic — see awards.py."""
    league_avg, _ = league_avg_overall()

    races = [
        {
            'id': 'mvp-kindelan', 'label': 'Premio Kindelan',
            'subtitle': 'MVP del bateador',
            'blurb': Markup(
                '<strong>Mejor bateador de la temporada.</strong> '
                'Puntaje base = <code>OPS × 100</code>, más bono de top-5 en '
                'AVG / HR / RBI (5·4·3·2·1 puntos), multiplicado por el lugar '
                'del equipo en la tabla (1º lugar = ×1.06, 8º = ×0.92).<br>'
                '<em>Califica:</em> <code>AB + BB ≥ 2 × juegos del equipo</code>.'
            ),
            'key_label': 'OPS', 'key_fmt': '%.3f',
            'entries': compute_kindelan_race(),
        },
        {
            'id': 'mvp-lazo', 'label': 'Premio Lazo',
            'subtitle': 'Cy Young del lanzador',
            'blurb': Markup(
                '<strong>Mejor lanzador de la temporada.</strong> '
                'Puntaje base = <code>max(0, 10 − ERA) × 10</code>, más bono '
                'de top-5 en SO / ERA / W, multiplicado por el lugar del '
                'equipo en la tabla.<br>'
                '<em>Califica:</em> <code>IP_outs ≥ 2.4 × juegos del equipo</code> '
                '(aproximadamente 2.4 innings por juego del equipo).'
            ),
            'key_label': 'ERA', 'key_fmt': '%.2f',
            'entries': compute_lazo_race(),
        },
        {
            'id': 'mvp-artesano', 'label': 'Premio al Artesano',
            'subtitle': 'Mejor abridor por consistencia',
            'blurb': Markup(
                '<strong>El abridor más completo.</strong> Cada apertura se '
                'puntúa con el <em>Game Score</em> de Bill James: '
                '<code>outs + 2·SO − 3·ER − 2·BB − 4·HR</code>.<br>'
                '<em>Calidad</em> = ≥ 18 outs y ≤ 3 ER. '
                '<em>Dominante</em> = ≥ 21 outs y ≤ 1 ER. '
                '<em>Fracaso</em> = &lt; 9 outs o ≥ 6 ER.<br>'
                'Puntaje total = suma de game scores + <strong>outs totales</strong> '
                '(premia durabilidad) + 10·dominantes − 15·fracasos + 2·racha QS. '
                'Bono top-5 en QS / DOM / pocos fracasos. '
                '<strong>Sin multiplicador de equipo.</strong><br>'
                '<em>Califica:</em> <code>role=\'rotation\'</code> con ≥ 2 aperturas '
                'o ≥ 15 outs totales.'
            ),
            'key_label': 'Avg GS', 'key_fmt': '%.1f',
            'entries': compute_artesano_race(),
        },
        {
            'id': 'mvp-clutch', 'label': 'Premio Clutch',
            'subtitle': 'Mejor en momentos decisivos',
            'blurb': Markup(
                '<strong>Momento de gloria.</strong> Solo cuentan '
                '<em>juegos decisivos</em>: margen final ≤ 2 carreras '
                '<em>o</em> rival entre los 4 mejores <strong>según el power '
                'ranking de la semana previa</strong> (no el ranking actual — '
                'evita juzgar juegos viejos con standings de hoy). Semanas sin '
                'ranking aun solo cuentan por margen cerrado.<br>'
                'Puntaje = <code>clutch_OPS × 100 × √(clutch_AB / 10)</code>. '
                'La raíz cuadrada premia volumen — 0.900 OPS en 40 AB bate a '
                '1.200 OPS en 3 AB.<br>'
                '<strong>Sin bono ni multiplicador de equipo</strong> — '
                'la fórmula ya combina calidad y volumen en un solo número.<br>'
                '<em>Califica:</em> ≥ 10 AB en juegos clutch.'
            ),
            'key_label': 'Clutch OPS', 'key_fmt': '%.3f',
            'entries': compute_clutch_race(),
        },
        {
            'id': 'mvp-five-tools', 'label': 'Cinco Herramientas',
            'subtitle': 'Jugador más completo',
            'blurb': Markup(
                '<strong>El bateador más balanceado.</strong> Tres herramientas, '
                'cada una mezcla 40% del rating del scout y 60% de la producción '
                'real, convertido a percentil de la liga:<br>'
                '&bull; <strong>Contacto</strong> = contact ratings + AVG<br>'
                '&bull; <strong>Poder</strong> = power ratings + ISO (SLG − AVG)<br>'
                '&bull; <strong>Velocidad</strong> = speed rating + carreras por '
                'veces-en-base (<code>R / (H + BB)</code>) — cuán seguido anota cuando '
                'llega a base<br>'
                'Puntaje final = <code>100 × media geométrica</code> de las tres '
                'herramientas. La geometría <em>castiga desbalance</em>: (0.9, 0.9, 0.3) '
                'pierde contra (0.7, 0.7, 0.7). Premia al cinco-herramientas real, no al '
                'especialista.<br>'
                'Bono top-5 en cada herramienta. <strong>Sin multiplicador de equipo.</strong>'
            ),
            'key_label': 'Balance', 'key_fmt': '%.3f',
            'entries': compute_five_tools_race(),
        },
        {
            'id': 'mvp-undercover', 'label': 'Premio Encubierto',
            'subtitle': f'Mejor jugador con OVR bajo {league_avg:.1f}',
            'blurb': Markup(
                '<strong>Joya escondida.</strong> Solo bateadores con '
                f'<strong>OVR &lt; {league_avg:.1f}</strong> (promedio de la liga) '
                'califican. Fórmula tipo Kindelan (OPS × 100 + bono top-5 AVG/HR/RBI) '
                'más bonus <code>+0.5 × (promedio − OVR)</code>: mientras más lejos '
                'del promedio, más mérito por superar la evaluación del scout.<br>'
                '<strong>Sin multiplicador de equipo.</strong><br>'
                '<em>Califica:</em> OVR bajo el promedio y '
                '<code>AB + BB ≥ 1 × juegos del equipo</code>.'
            ),
            'key_label': 'OPS', 'key_fmt': '%.3f',
            'entries': compute_undercover_race(),
        },
    ]
    return render_template('mvp_race.html', races=races)
