# MVP Cuba 2011 Tournament Tracker

Baseball tournament tracker for a simulated Cuban National Series season played in MVP Baseball 2005. Two owners (Ernesto and Junior) each control 4 teams. Tracks standings, schedules, game results, player stats, draft, playoffs, and "antesala" (pre-game show).

## Stack

- **Flask** with app factory pattern (`create_app()`) and **Blueprints**
- Raw **sqlite3** (no SQLAlchemy), with `sqlite3.Row` factory
- **Jinja2** server-rendered templates with reusable component macros
- **SQLite** database at `torneo.db` in project root (WAL mode)
- **Python 3**, dependencies: `flask`, `openpyxl`

## Engineering Principles

Follow `flask-sqlite-engineering-principles.md` in this repo. Key rules:
- Max 300 lines per file, single responsibility
- Type hints everywhere
- Blueprints for every feature
- Component-based Jinja2 macros (reusable, no copy-paste HTML)
- Fat models / thin views — routes are glue, logic in services
- SQLite: WAL mode, `PRAGMA foreign_keys=ON`, short write transactions
- No hardcoded secrets, env-based config
- Fix tech debt immediately, DRY on 2nd occurrence

## Project Structure

```
Torneo/
├── app.py                        # create_app() factory
├── config.py                     # BaseConfig, DevConfig, ProdConfig
├── db.py                         # get_db(), close_db(), init_app()
├── blueprints/
│   ├── main/                     # / (standings + recent games)
│   ├── teams/                    # /team/<short>
│   ├── players/                  # /player/<id>, /jugadores
│   ├── schedule/                 # /schedule
│   ├── games/                    # /game/new/<id>, /game/save
│   ├── draft/                    # /draft
│   ├── playoffs/                 # /playoffs
│   ├── leaders/                  # /leaders
│   ├── antesala/                 # /antesala
│   └── weekly/                   # /weekly, /weekly/<week_num>
├── services/
│   ├── standings.py              # get_standings(), get_all_teams()
│   ├── weekly.py                 # weekly summaries, awards, tweets
│   ├── power_rankings.py         # compute_power_rankings()
│   ├── game_import.py            # insert_game() + validate_game()
│   └── attributes_import.py      # bulk_upsert()
├── lib/utils.py                  # format_ip() — Jinja2 global
├── templates/
│   ├── base.html
│   ├── components/               # Reusable macros: logo_img, team_link, game_card,
│   │                             #   game_score, pitcher_credits, pitcher_select,
│   │                             #   leaderboard_table, tweet_item, owner_badge,
│   │                             #   empty_state, player_cell, stat_box, section_label,
│   │                             #   series_table
│   ├── errors/                   # 404.html, 500.html
│   └── *.html                    # Page templates
├── static/
│   ├── style.css                 # Design system (CSS variables, bento grid, utilities)
│   ├── app.js                    # Sidebar toggle, card animations, sortable tables
│   └── graphics/                 # Team logos, player photos, banners
├── schema.sql                    # Reference DDL only — do NOT run on populated DB
├── scripts/
│   ├── create_tournament.py
│   └── crop_attributes.py
├── DESIGN.md                     # UI design spec
└── torneo.db                     # Live SQLite database
```

Each blueprint has `__init__.py`, `routes.py`, and `services.py` (except weekly which has services in `services/weekly.py`).

## UI Component Patterns

- **All logos** go through `logo_img(file, css_class, alt)` macro — never raw `<img>` tags for logos
- **Logo sizes**: `inline-logo` (64px default), `inline-logo-md` (32px), `inline-logo-sm` (16px)
- **Logo bleed**: Oversized logos cropped by container's `overflow: hidden`. Used in game cards (horizontal) and standings rows (vertical + left). See DESIGN.md §5.5.
- **`{% block scripts %}`** in `base.html` runs after `app.js` — always put page JS there, not in `{% block content %}` (app.js won't be loaded yet)
- **Sortable tables**: Add `data-sort="num"` or `data-sort="text"` to `<th>`, call `initSortableTable(el)` in `{% block scripts %}`
- **Component-first**: No copy-paste HTML. If markup appears in 2+ templates, extract to a macro in `templates/components/`

## Database Schema (torneo.db)

| Table | Key columns / gotchas |
|-------|----------------------|
| `teams` | `short_name` (not `short`), `name`, `full_name`, `owner`, `color_primary`, `logo_file` |
| `players` | `name`, `position`, `bats_throws` (not separate), `role` (lineup/bench/rotation/bullpen), `bullpen_role`, `lineup_order`, `is_drafted` |
| `draft_picks` | 24 picks (3 rounds x 8 teams) linking to player IDs |
| `schedule` | `game_num` (not `game_number`), `week_num`, `phase`, `series_game` |
| `games` | score, hits, errors, W/L/S pitcher IDs, `home_linescore`/`away_linescore` |
| `player_attributes` | power, contact, speed, pitch ratings. Pitches: fastball, slider, curveball, sinker, changeup, splitter, screwball, cutter, curveball_dirt |
| `batting_stats` | Per-game: AB, R, H, doubles, triples, HR, RBI, BB, SO, SB |
| `pitching_stats` | Per-game: `IP_outs` (total outs, not innings — use `format_ip()`), H, R, ER, BB, SO, HR_allowed, W, L, SV, pitches |
| `analysts` | 3 commentator personalities with favorite/hated teams |
| `analyst_tweets` | Game/weekly commentary (week_num for weekly) |
| `analyst_game_picks` | Per-game winner predictions: `analyst_id`, `schedule_id`, `picked_team_id`, `week_num`. UNIQUE(analyst_id, schedule_id) |
| `weekly_awards` | POTW, Power Rankings (JSON), `game_of_week_id` per week |

## Domain Rules

- **8 teams**: Ernesto (GRA, SSP, PRI, LTU) / Junior (SCU, VCL, IND, CAV)
- **Regular season:** 96 games (each team plays 24 — round-robin)
- **Playoffs:** Top 4 advance. Best-of-5 semis and finals
- **Draft:** 3 rounds, 8 picks each. Players marked `is_drafted=1`
- **Team short names** are 3-letter codes used in URLs: `/team/GRA`, etc.

## Game Data Entry Workflow

Games are entered from MVP Baseball 2005 box score screenshots in `Games/game{N}/`.

### Files per game folder
- **6 PNG screenshots** (timestamped, chronological order)
- **lanzamientos.txt** — pitch counts per pitcher, grouped by team

### Screenshot order (always 6)
| # | Content |
|---|---------|
| 1 | **Away batting** (top half: 5-6 players) + linescore header |
| 2 | **Away batting** (remaining + totals + extras: 2B, 3B, HR, IMP, SH, SB, E) |
| 3 | **Home batting** (top half) |
| 4 | **Home batting** (remaining + totals + extras) |
| 5 | **Away pitching** |
| 6 | **Home pitching** |

### MVP 2005 column mappings

**Batting (Spanish -> DB):**
VB=AB, C=R, H=H, IMP=RBI, BB=BB, SO=SO, AVE=H/AB this game (verification only)

Extra-base hits in summary (screenshots 2 & 4): `2B:`, `3B:`, `HR:` (player names), `IMP:` (RBI attribution), `Corrido de Base:` (SB), `Fildeo: E:` (errors)

**Pitching (Spanish -> DB):**
INN=IP_outs (convert `5.1` -> 16 outs), H=H, C=R, CL=ER, BB=BB, SO=SO, HR=HR_allowed, PCL=ERA (skip)

W/L/S shown as `(W)`, `(L)`, `(S)` next to pitcher name.

### How to enter games — use `insert_game()`!

**Always use `services/game_import.py :: insert_game()`** — never raw SQL. It resolves player names, validates totals via `validate_game()`, and supports upsert.

```python
from services.game_import import insert_game

insert_game(
    schedule_id=5,
    home_runs=0, away_runs=2, home_hits=4, away_hits=4,
    home_errors=0, away_errors=0,
    wp=("A. Mora", "CAV"), lp=("C. Licea", "GRA"), sv=("P. Echemendia", "CAV"),
    batting=[
        {"name": "A. Sanchez", "team": "CAV", "AB": 4, "R": 0, "H": 1, "2B": 0, "3B": 0, "HR": 0, "RBI": 0, "BB": 0, "SO": 2, "SB": 0},
        # ... all batters for both teams
    ],
    pitching=[
        {"name": "A. Mora", "team": "CAV", "IP": "5.0", "H": 3, "R": 0, "ER": 0, "BB": 0, "SO": 4, "HR": 0, "W": 1, "L": 0, "SV": 0, "pitches": 49},
        # ... all pitchers for both teams
    ],
    home_linescore="0,0,0,0,0,0,0,0,0",
    away_linescore="0,0,0,1,0,0,0,0,1",
)
```

### Cross-validation system

`insert_game()` calls `validate_game()` after saving and **raises `ValueError`** if any check fails. This catches pixel misreads before bad data is silently accepted.

**7 automated cross-checks:**
1. Batting R/H totals match game header values
2. Pitching H/R/BB/SO must equal opposing team's batting totals
3. Linescore sums match total runs
4. IP outs sufficient (>= 27, or >= 24 for visiting pitchers when home team wins)
5. Extra-base hits (2B+3B+HR) <= total hits per player
6. ER <= R for every pitcher
7. Exactly 1 W, 1 L, at most 1 SV

### Optimal parsing order

Read all 6 screenshots + lanzamientos.txt in parallel, then parse:

1. **Screenshots 2 & 4 first** (batting totals + extras) — hard constraints: total AB/R/H/RBI/BB/SO, who had 2B/3B/HR, who drove in runs, linescore
2. **Screenshots 5 & 6 next** (pitching) — fewer rows, clearer numbers. H/R/BB/SO cross-check against opposing batting
3. **Screenshots 1 & 3 last** (individual batting) — heavily constrained by now:
   - H per player from AVE column (AVE = H/AB, this game only)
   - 2B/3B/HR already assigned from extras
   - RBI already assigned from IMP list
   - Only R, BB, SO remain ambiguous — but totals + pitching constrain them

### Common pitfalls
- Extra-inning games: linescore scrolls right, early innings may be hidden
- `IP_outs` conversion: `5.1` IP = 16 outs. Formula: `int(IP) * 3 + decimal_part`
- Player names use `F. LastName` format — must match `players.name` exactly
- Pitches from lanzamientos.txt -> `pitches` column in `pitching_stats`

### lanzamientos.txt format

```
TEAM_SHORT
PitcherLastName pitchCount

TEAM_SHORT
PitcherLastName pitchCount
```

## Weekly Content Workflow

When generating content for week N (after week N games are played):

1. Run `python weekly.py N` — prints summary + upcoming week N+1 games with rankings
2. Use output to generate: POTW, power rankings, analyst tweets
3. Save via `save_weekly_awards()`, `save_weekly_tweets()`
4. **Generate predictions for week N+1:**
   - `generate_game_picks(N+1)` — uses week N power rankings + analyst personality
   - `save_game_picks(N+1, picks)` — stores in `analyst_game_picks`
   - `pick_game_of_week(N+1)` — closest power ranking matchup
   - Save game_of_week_id via `save_weekly_awards(N+1, ..., game_of_week_id=gotw)`
5. Predictions show on `/schedule` — analyst avatars next to predicted winner, gold badge for Game of the Week

### Analyst prediction logic
- Default: pick higher-ranked team (from previous week's power rankings)
- Favorite team playing → always pick favorite
- Hated team playing (no favorite conflict) → always pick opponent

## Player Attributes Entry Workflow

Attributes are entered from MVP 2005 roster screenshots. **All 8 teams are entered.**

### User workflow
1. User specifies team, takes screenshots in `C:\Users\ernes\Videos\Captures`
2. Run `python scripts/crop_attributes.py` — saves crops to `Captures/cropped/`
3. Read cropped images, parse attributes, insert with `bulk_upsert()`

### Screenshot layout

**Batter ("Orden Al Bate"):** `POS - Full Name - #Number`, then vs ZUR (power_vs_l, contact_vs_l) / vs DER (power_vs_r, contact_vs_r) / Vel (speed)

**Pitcher ("Rotacion de Pitcheo"):** `POS - Full Name - #Number`, ESTAMINA (stamina), then pitch types:
R4C=fastball, SLD=slider, CRV=curveball, SNK=sinker, TND=changeup, SPL=splitter, SCR=screwball, CBB=curveball_dirt, RCT=cutter

### How to insert — use `bulk_upsert()`!

**Always use `services/attributes_import.py :: bulk_upsert()`** — resolves names, handles insert/update.

```python
from services.attributes_import import bulk_upsert
bulk_upsert("SSP", [
    {"name": "Y. Mendoza", "power_vs_l": 54, "contact_vs_l": 73, "power_vs_r": 70, "contact_vs_r": 72, "speed": 75},
    {"name": "D. Hinojosa", "stamina": 81, "fastball": 81, "sinker": 72, "curveball": 77, "slider": 72},
])
```

### Notes
- If a player isn't in DB, add to `players` first: `INSERT INTO players (name, team_id, position, role, bullpen_role) VALUES (?, ?, ?, ?, ?)`
- Extract full names from screenshot headers and update `players.full_name`
- **Duplicate names on same team** (e.g., two Y. Perez on VCL): use `upsert_attributes(player_id, attrs)` with specific player ID
- `/jugadores` page shows all players with attributes, sortable/filterable, color-coded (green >= 85, gold >= 70)
