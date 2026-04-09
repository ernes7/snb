# MVP Cuba 2011 Tournament Tracker

Baseball tournament tracker for a simulated Cuban National Series season played in MVP Baseball 2005. Two owners (Ernesto and Junior) each control 4 teams. The app tracks standings, schedules, game results, player stats, a draft system, playoffs, and an "antesala" (pre-game show) with analyst commentary.

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
TOrneo/
├── app.py                          # create_app() factory, blueprint registration
├── config.py                       # BaseConfig, DevConfig, ProdConfig
├── db.py                           # get_db(), close_db(), init_app() — WAL mode
├── blueprints/
│   ├── main/                       # / (index, standings)
│   │   ├── __init__.py             # main_bp
│   │   ├── routes.py
│   │   └── services.py             # get_recent_games()
│   ├── teams/                      # /team/<short>
│   │   ├── __init__.py             # teams_bp
│   │   ├── routes.py
│   │   └── services.py             # get_team(), get_roster(), team leaders
│   ├── players/                    # /player/<int:player_id>
│   │   ├── __init__.py             # players_bp
│   │   ├── routes.py
│   │   └── services.py             # get_player(), batting/pitching logs & totals
│   ├── schedule/                   # /schedule
│   │   ├── __init__.py             # schedule_bp
│   │   ├── routes.py
│   │   └── services.py             # get_schedule_games()
│   ├── games/                      # /game/new/<id>, /game/save (POST)
│   │   ├── __init__.py             # games_bp
│   │   ├── routes.py
│   │   ├── services.py             # get_game_form_data(), save_game(), get_game_detail()
│   │   └── boxscore_services.py    # get_boxscore_form_data(), save_boxscore()
│   ├── draft/                      # /draft
│   │   ├── __init__.py             # draft_bp
│   │   ├── routes.py
│   │   └── services.py             # get_draft_picks(), get_draft_teams()
│   ├── playoffs/                   # /playoffs
│   │   ├── __init__.py             # playoffs_bp
│   │   ├── routes.py
│   │   └── services.py             # get_series()
│   ├── leaders/                    # /leaders
│   │   ├── __init__.py             # leaders_bp
│   │   ├── routes.py
│   │   └── services.py             # batting/pitching leader queries
│   ├── antesala/                   # /antesala
│   │   ├── __init__.py             # antesala_bp
│   │   ├── routes.py
│   │   └── services.py             # analysts, predictions, tweets
│   └── weekly/                     # /weekly
│       ├── __init__.py             # weekly_bp
│       └── routes.py
├── services/
│   ├── standings.py                # get_standings(), get_all_teams() — shared
│   ├── weekly.py                   # weekly summaries, awards, tweets
│   ├── game_import.py              # insert_game() — complete game entry from box scores
│   └── attributes_import.py        # bulk_upsert() — player attributes from roster screenshots
├── lib/
│   └── utils.py                    # format_ip() — registered as Jinja2 global
├── templates/
│   ├── base.html                   # Master layout with nav
│   ├── components/                 # Reusable Jinja2 macros
│   │   ├── logo_img.html           # logo_img(logo_file, css_class, alt)
│   │   ├── team_link.html          # team_link(short, name, color, logo_file)
│   │   ├── stat_box.html           # stat_box(value, label)
│   │   ├── game_score.html         # game_score(home, away, h_color, a_color)
│   │   ├── pitcher_credits.html    # pitcher_credits(wp, lp, sv)
│   │   ├── owner_badge.html        # owner_badge(owner)
│   │   ├── empty_state.html        # empty_state(message)
│   │   ├── player_cell.html        # player_cell(player, show_full_name)
│   │   ├── section_label.html      # section_label(text)
│   │   └── series_table.html       # series_table(title, games)
│   ├── errors/
│   │   ├── 404.html
│   │   └── 500.html
│   ├── index.html                  # Homepage: standings + recent games
│   ├── team.html                   # Team detail: roster, batting/pitching leaders
│   ├── player.html                 # Player detail: attributes, draft info, game log
│   ├── schedule.html               # 96-game regular season schedule
│   ├── game_form.html              # Enter/edit game results (score, pitchers)
│   ├── draft.html                  # Draft picks tracker + team rankings
│   ├── playoffs.html               # Playoff bracket (semi A, semi B, final)
│   ├── leaders.html                # Statistical leaders (AVG, HR, RBI, ERA)
│   ├── antesala.html               # Analysts, predictions, tweets
│   └── weekly.html                 # Weekly recap: POTW, power rankings, tweets
├── static/
│   ├── style.css                   # Single stylesheet (~400 lines, CSS variables)
│   └── graphics/                   # Team logos (PNG), player photos, banners
├── schema.sql                      # Reference DDL for all tables (do NOT run on populated DB)
├── weekly.py                       # CLI: python weekly.py <week_num> — prints weekly summary
├── scripts/
│   ├── create_tournament.py        # Generates Excel workbook with tournament info
│   └── crop_attributes.py          # Crops roster screenshots to attribute area
├── torneo.db                       # SQLite database (populated, git-ignored)
├── Dockerfile                      # Python 3.12 + gunicorn production image
├── docker-compose.yml              # Single-service with volume for DB persistence
├── requirements.txt                # flask, openpyxl, gunicorn
└── flask-sqlite-engineering-principles.md
```

## Routes (blueprint-qualified)

| Route | Endpoint | Purpose |
|-------|----------|---------|
| `/` | `main.index` | Standings table + last 10 games |
| `/team/<short>` | `teams.team` | Team roster, record, batting/pitching leaders |
| `/player/<int:player_id>` | `players.player` | Full player page with attributes, stats, game log |
| `/schedule` | `schedule.schedule` | Regular season schedule with scores |
| `/game/new/<int:schedule_id>` | `games.game_new` | Game entry/edit form |
| `/game/save` (POST) | `games.game_save` | Save game result |
| `/draft` | `draft.draft` | Draft picks display |
| `/playoffs` | `playoffs.playoffs` | Playoff bracket |
| `/leaders` | `leaders.leaders` | League statistical leaders |
| `/antesala` | `antesala.antesala` | Analyst show: predictions + tweets |
| `/weekly` | `weekly.weekly` | Weekly recap: POTW, rankings, tweets |
| `/weekly/<int:week_num>` | `weekly.weekly` | Weekly recap for specific week |
| `/jugadores` | `players.all_players` | All players database with attributes |

## Database Schema (torneo.db)

| Table | Purpose |
|-------|---------|
| `teams` | 8 teams with rankings, colors, logos, owner (Ernesto/Junior) |
| `players` | 71 players — role: lineup/bench/rotation/bullpen |
| `draft_picks` | 24 picks (3 rounds, 8 teams) linking to player IDs |
| `schedule` | 96 regular + playoff games, phase: regular/semi_a/semi_b/final |
| `games` | Results: score, hits, errors, W/L/S pitchers |
| `player_attributes` | Power, contact, speed, pitch ratings per player |
| `batting_stats` | Per-game: AB, R, H, 2B, 3B, HR, RBI, BB, SO, SB |
| `pitching_stats` | Per-game: IP_outs, H, R, ER, BB, SO, HR, W, L, SV |
| `analysts` | 4 commentator personalities with favorite/hated teams |
| `analyst_predictions` | Pre-season predictions per analyst |
| `analyst_tweets` | Game/weekly commentary per analyst (week_num for weekly) |
| `weekly_awards` | Player of the Week + Tele Rebelde Power Rankings per week |

**IP_outs:** Pitching innings are stored as total outs (not innings). Use `format_ip()` to display (e.g., 19 outs = "6.1").

## Key Architecture Patterns

- **App factory:** `create_app()` in `app.py` — creates app, registers blueprints, error handlers, Jinja2 globals
- **DB connection:** `db.get_db()` — request-scoped via Flask `g`, WAL mode, foreign keys ON, busy timeout 5s
- **Shared services:** `services/standings.py` — used by main, teams, and playoffs blueprints
- **Thin routes:** Routes call service functions and pass results to templates
- **Component macros:** Reusable Jinja2 macros in `templates/components/` — imported with `{% from %}` syntax

## Domain Rules

- **8 teams**, split between two owners: Ernesto (GRA, SSP, PRI, LTU) and Junior (SCU, VCL, IND, CAV)
- **Regular season:** 96 games (each team plays 24 — round-robin)
- **Playoffs:** Top 4 advance. Best-of-5 semis and finals
- **Draft:** 3 rounds, 8 picks each (24 total). Players marked `is_drafted=1`
- **Team short names** are 3-letter codes used in URLs: `/team/GRA`, `/team/IND`, etc.

## Running

```bash
pip install flask openpyxl
python app.py         # Runs on http://localhost:5000
```

## Schema Reference

`schema.sql` contains the full DDL for all tables. It is for reference only — do NOT run it against a populated database (it drops all tables). The live database is `torneo.db`; keep a backup.

## Game Data Entry Workflow

Games are entered from MVP Baseball 2005 box score screenshots stored in `Games/game{N}/`.

### Files per game folder
- **6 PNG screenshots** (timestamped, chronological order)
- **lanzamientos.txt** — pitch counts per pitcher, grouped by team

### Screenshot order (always 6, in this sequence)
| # | Content |
|---|---------|
| 1 | **Away team batting** (top half: 5-6 players) + linescore header |
| 2 | **Away team batting** (remaining players + totals + extras: 2B, 3B, HR, IMP, SH, SB, E) |
| 3 | **Home team batting** (top half) |
| 4 | **Home team batting** (remaining + totals + extras) |
| 5 | **Away team pitching** |
| 6 | **Home team pitching** |

### MVP 2005 column mappings

**Batting (Spanish → DB):**
| UI Column | Meaning | DB Column |
|-----------|---------|-----------|
| VB | Veces al Bate | AB |
| C | Carreras | R |
| H | Hits | H |
| IMP | Impulsadas | RBI |
| BB | Bases por Bolas | BB |
| SO | Ponches | SO |
| AVE | Average (this game only) | — |

Extra-base hits appear in the summary section of screenshots 2 & 4:
- `2B:` → doubles | `3B:` → triples | `HR:` → home runs
- `IMP:` → RBI attribution (player names + count)
- `SH:` → sacrifice hits (not stored in DB)
- `Corrido de Base:` → SB (stolen bases)
- `Fildeo: E:` → errors (not per-player in DB)

**Pitching (Spanish → DB):**
| UI Column | Meaning | DB Column |
|-----------|---------|-----------|
| INN | Innings Pitched | IP_outs (convert: `5.1` → 16 outs) |
| H | Hits | H |
| C | Carreras | R |
| CL | Carreras Limpias | ER |
| BB | Bases por Bolas | BB |
| SO | Ponches | SO |
| HR | Home Runs | HR_allowed |
| PCL | ERA (this game only) | — |

W/L/S shown as `(W)`, `(L)`, `(S)` next to pitcher name.

### lanzamientos.txt format

```
TEAM_SHORT
PitcherLastName pitchCount
PitcherLastName pitchCount

TEAM_SHORT
PitcherLastName pitchCount
```

### How to enter games — use `insert_game()`!

**Always use `services/game_import.py :: insert_game()`** — never raw SQL. It resolves player names to IDs, validates totals, and supports upsert.

```python
from services.game_import import insert_game

insert_game(
    schedule_id=5,
    home_runs=0, away_runs=2,
    home_hits=4, away_hits=4,
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

### Optimal parsing order (read all 6 screenshots, then parse in this order)

Read all 6 screenshots + lanzamientos.txt in parallel. Then parse in this order to minimize ambiguity:

1. **Screenshots 2 & 4 first** (batting totals + extras) — gives you hard constraints:
   - Total AB, R, H, RBI, BB, SO per team
   - Exactly who had 2B, 3B, HR (from extras list)
   - Exactly who drove in runs (IMP list with counts)
   - Linescore from header
2. **Screenshots 5 & 6 next** (pitching) — fewer rows, clearer numbers:
   - Pitching H/R/BB/SO must equal opposing batting totals (second cross-check)
   - W/L/S markers identify game pitchers
   - IP values confirm game length
3. **Screenshots 1 & 3 last** (individual batting) — now heavily constrained:
   - H per player: already known from AVE column (AVE = H/AB, this game only)
   - 2B/3B/HR: already assigned from extras
   - RBI: already assigned from IMP list
   - Only R, BB, SO remain ambiguous — but totals + pitching constrain them
   - When a pixel is ambiguous (0 vs 1?), there's usually only one valid option left

### Cross-checking rules
1. **AVE column = hits/AB for THIS GAME only** (not cumulative). Use it to confirm H per player.
2. **Totals line** (screenshot 2 & 4): verify AB, R, H, RBI, BB, SO sums.
3. **Extra-base summary** tells you exactly who had 2B/3B/HR — distribute from there.
4. **Pitching H/R/SO totals must match opposing batting totals.**
5. **Extra-inning games**: linescore may scroll, hiding early innings. Compute missing innings from total runs minus visible innings.

### Common pitfalls
- Extra-inning games: linescore scrolls right, innings 1-2 may be hidden. Ask user if split matters.
- `IP_outs` conversion: `5.1` IP = 16 outs (not 5.1 * 3). Formula: `int(IP) * 3 + decimal_part`.
- Player names in screenshots use `F. LastName` format — must match `players.name` exactly.
- Pitches from lanzamientos.txt → `pitches` column in `pitching_stats`.

## Player Attributes Entry Workflow

Attributes are entered from MVP 2005 roster screenshots, one team at a time.

### User workflow
1. User tells you the team (e.g. "SSP")
2. User takes screenshots of each player in `C:\Users\ernes\Videos\Captures`
3. Run `python scripts/crop_attributes.py` — saves cropped copies to `Captures/cropped/`
4. Read cropped images, parse attributes, insert with `bulk_upsert()`
5. User deletes screenshots and repeats for next team

### Screenshot layout

**Batter screen ("Orden Al Bate"):**
```
POS - Full Name - #Number
vs ZUR   Pod XX   vs DER   Pod XX
         Con XX            Con XX
         Vel XX            Vel XX
```
- vs ZUR = vs Left → power_vs_l, contact_vs_l
- vs DER = vs Right → power_vs_r, contact_vs_r
- Vel = speed (same both sides)

**Pitcher screen ("Rotacion de Pitcheo"):**
```
POS - Full Name - #Number
ESTAMINA  [pitch1] XX  [pitch2] XX
XX        [pitch3] XX  [pitch4] XX
          [pitch5] XX
```
Pitch type abbreviations → DB columns:
- R4C → fastball | SLD → slider | CRV → curveball
- SNK → sinker | TND → changeup | SPL → splitter | SCR → screwball
- ESTAMINA → stamina

### How to insert — use `bulk_upsert()`!

**Always use `services/attributes_import.py :: bulk_upsert()`** — it resolves player names, handles insert/update.

```python
from services.attributes_import import bulk_upsert

batters = [
    {"name": "Y. Mendoza", "power_vs_l": 54, "contact_vs_l": 73, "power_vs_r": 70, "contact_vs_r": 72, "speed": 75},
    # ... all batters
]
pitchers = [
    {"name": "D. Hinojosa", "stamina": 81, "fastball": 81, "sinker": 72, "curveball": 77, "slider": 72},
    # ... all pitchers
]
bulk_upsert("SSP", batters + pitchers)
```

### Reading order for speed
1. Read ALL cropped images in parallel (batch of 8)
2. Parse batter screens: name → power_vs_l, contact_vs_l, power_vs_r, contact_vs_r, speed
3. Parse pitcher screens: name → stamina + pitch type values
4. Build single `bulk_upsert()` call with all entries
5. If a player in the screenshot isn't in the DB, add them to `players` first

### Player Database UI
- Route: `/jugadores` (endpoint: `players.all_players`)
- Shows all players with attributes, sortable columns, filterable by team/role/owner
- Attribute values color-coded: green (≥85), gold (≥70)
