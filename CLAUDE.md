# MVP Cuba 2011 Tournament Tracker

Baseball tournament tracker for a simulated Cuban National Series season played in MVP Baseball 2005. Two owners (Ernesto and Junior) each control 4 teams. Tracks standings, schedules, game results, player stats, draft, playoffs, antesala (pre-game show), and weekly recaps.

**League rules (tiebreakers, awards, draft, playoffs) live in [RULES.md](RULES.md).**

## Stack

- **Flask** with app factory pattern (`create_app()`) and **Blueprints**
- Raw **sqlite3** (no SQLAlchemy), with `sqlite3.Row` factory
- **Jinja2** server-rendered templates with reusable component macros
- **SQLite** database at `torneo.db` in project root (WAL mode)
- **Python 3**, dependencies: `flask`, `openpyxl`

## Engineering Principles

Follow `flask-sqlite-engineering-principles.md`. Key rules:
- Max 300 lines per file, single responsibility
- Type hints everywhere, Blueprints for every feature
- Component-based Jinja2 macros (no copy-paste HTML)
- Fat models / thin views — routes are glue, domain logic lives in `models/` (queries rooted on one entity) and `services/` (cross-entity business rules)
- SQLite: WAL mode, `PRAGMA foreign_keys=ON`, short write transactions
- **Never DELETE database rows when refactoring UI** — modify queries/templates instead

## Project Structure

```
Torneo/
├── app.py                        # create_app() factory
├── config.py                     # BaseConfig, DevConfig, ProdConfig
├── db.py                         # get_db(), close_db(), init_app()
├── blueprints/
│   ├── main/                     # / (standings + recent games grid)
│   ├── teams/                    # /team/<short>
│   ├── players/                  # /player/<id>, /jugadores
│   ├── schedule/                 # /schedule (calendar, picks, GOTW, starters)
│   ├── games/                    # /game/<id>, /game/new/<id>, /game/save
│   ├── draft/                    # /draft
│   ├── playoffs/                 # /playoffs
│   ├── leaders/                  # /leaders (player leaderboards)
│   ├── team_stats/               # /team-stats (team-level leaderboards)
│   ├── mvp_race/                 # /mvp-race (Premio Kindelan + Premio Lazo)
│   ├── antesala/                 # /antesala (analysts, predictions, tweet feed)
│   ├── versus/                   # /versus (head-to-head matchup grid)
│   ├── weekly/                   # /weekly, /weekly/<week_num>
│   └── periodico/                # /periodico (newspaper "En Tres y Dos")
├── services/
│   ├── standings.py              # get_standings()
│   ├── player_stats.py           # get_all_batting_lines(), get_all_pitching_lines() — shared aggregates
│   ├── weekly.py                 # weekly summaries, tweets, predictions, game picks
│   ├── power_rankings.py         # compute_power_rankings()
│   ├── game_import.py            # insert_game() + validate_game()
│   └── attributes_import.py      # bulk_upsert()
├── models/                       # Domain models — OOP layer over DB rows
│   ├── base.py                   # RowModel (exposes sqlite3.Row columns as attrs)
│   ├── team.py                   # Team + TeamRecord — records, aggregates, H2H, batch methods
│   ├── player.py                 # Player — lines, logs, sparklines, draft, attrs
│   ├── week.py                   # Week + WeekCompletion — weekly scopes
│   └── game.py                   # Game + recent_games/week_games helpers
├── lib/
│   ├── utils.py                  # format_ip() — Jinja2 global
│   ├── stats.py                  # BattingLine, PitchingLine — rate stat source of truth
│   ├── season.py                 # GAMES_PER_WEEK, TOTAL_WEEKS, Phase, week_game_range
│   └── scoring.py                # MVP multipliers, analyst weights, power-ranking weights
├── templates/
│   ├── base.html                 # Layout: sidebar, {% block content %}, {% block scripts %}
│   ├── components/               # Reusable macros (see UI Components below)
│   ├── errors/                   # 404.html, 500.html
│   └── *.html                    # Page templates
├── scripts/
│   ├── query.py                  # Ad-hoc SQL runner (replaces sqlite3 CLI)
│   ├── finalize_week.py          # Post-week automation (rankings, picks, GotW)
│   └── preprocess_cv2.py         # Fallback image preprocessor (CLAHE + Lanczos)
├── static/
│   ├── style.css                 # Design system (see DESIGN.md)
│   ├── mobile.css                # Responsive/mobile overrides
│   ├── app.js                    # Sidebar toggle, card animations, initSortableTable()
│   └── graphics/                 # Team logos, player photos, analyst avatars, banners
├── schema.sql                    # Reference DDL only — do NOT run on populated DB
├── weekly.py                     # CLI: python weekly.py <week_num>
├── requirements.txt              # Python dependencies
├── DESIGN.md                     # UI design spec (logo bleed, stat-num, etc.)
└── torneo.db                     # Live SQLite database
```

## UI Component Patterns

| Component | Macro | Purpose |
|-----------|-------|---------|
| `logo_img` | `logo_img(file, css_class, alt)` | All logos — never raw `<img>` for logos |
| `team_link` | `team_link(short, name, color, logo)` | Clickable team name + logo |
| `game_card` | `game_card(g, link)` | Game result card with logo bleed |
| `tweet_item` | `tweet_item(tweet)` | Tweet with likes, replies, hashtag |
| `pitcher_credits` | `pitcher_credits(wp, lp, ...)` | W/L pitcher line |
| `pitcher_select` | `pitcher_select(name, id, ...)` | Pitcher dropdown (game form) |
| `leaderboard_table` | `leaderboard_table(title, ...)` | Stat leader table (flexible columns) |
| `stat_box` | `stat_box(value, label, animate)` | Stat display box (animate=False for IP, G-P, non-numeric) |
| `sparkline` | `sparkline(points)` | Inline SVG trend chart (self-normalized) |
| `tabs` | `tab_group(tabs, aria_label)` | Segmented-control tabbed interface (`{% call %}` content injection) |
| `empty_state` | `empty_state(message)` | Empty content placeholder |

**Key patterns:**
- **Logo sizes**: `inline-logo` (64px), `inline-logo-md` (32px), `inline-logo-sm` (16px)
- **Logo bleed**: Oversized logos cropped by `overflow: hidden`. See DESIGN.md §5.5
- **`{% block scripts %}`**: Page JS goes here (after app.js loads), not in `{% block content %}`
- **Sortable tables**: `data-sort="num|text"` on `<th>` + `initSortableTable(el)` in `{% block scripts %}`
- **`stat-num` class**: Barlow Condensed, `--text-2xl`, bold — for all prominent numbers

## Stat Calculations — `lib/stats.py`

**All rate stats come from two frozen dataclasses in `lib/stats.py`:**

- **`BattingLine`** — holds counting stats (`AB, R, H, doubles, triples, HR, RBI, BB, SO, SB`) and exposes `AVG`, `OBP`, `SLG`, `OPS`, `TB`, `ISO`, `singles` as `@property`.
- **`PitchingLine`** — holds `IP_outs, H, R, ER, BB, SO, HR_allowed, W, L, SV` and exposes `ERA`, `WHIP`, `K9`.

**Rules (load-bearing):**
- **Never reimplement AVG/OBP/SLG/OPS/ERA/WHIP/K9 math** anywhere — not in SQL, not in services, not in templates. If you need a rate stat, build a `BattingLine`/`PitchingLine` and read the property.
- `BattingLine.from_row(sqlite3.Row | dict)` is the canonical constructor — any query that returns SUM() columns with the expected names can be wrapped.
- **OBP is an approximation**: `(H + BB) / (AB + BB)` — we don't track HBP or SF. OPS is computed from unrounded OBP + SLG internally, so don't try to recompute it from the rounded `obp`/`slg` properties.
- Services returning totals should return `BattingLine`/`PitchingLine` (or `None`), not dicts. Templates access `.AVG`, `.OPS`, `.ERA` via attribute syntax.
- **Shared per-player aggregates** live in `services/player_stats.py`: `get_all_batting_lines()` / `get_all_pitching_lines()` return list-of-dicts with player/team identity fields plus all counting and rate stats merged in (dict form so the `leaderboard_table` macro's `p[key]` subscript access keeps working). Both `/leaders` and `/mvp-race` consume these — don't duplicate the aggregate SQL.

## Domain Models — `models/`

All entity-rooted queries live on the model, not in blueprint services. Routes call `Team.get()`, `Player.get_with_team()`, `Week(n).top_batters()` etc. Templates use attribute access (`team.name`, `stats.wins`) — `RowModel` wraps a `sqlite3.Row` and falls through attribute lookups to the row's columns, so existing templates work unchanged.

**When adding a new aggregate**: add it to the relevant model, not to a blueprint service. If two models need it (e.g. "games played this week among these teams"), put it in `services/`.

**Key entry points** (never duplicate these queries elsewhere):
- `Team.get(short) / get_by_id(id) / all()` — fetch
- `Team.record(through_week=, phase=) → TeamRecord` — W/L/RS/RA for one team
- `Team.records_all(through_week=) / records_for_weeks(start, end)` — batch records dict
- `Team.batting_totals(through_week=) / pitching_totals(through_week=) → BattingLine/PitchingLine`
- `Team.team_stats_all(through_week=) → (dict[tid, BattingLine], dict[tid, PitchingLine])` — one-shot batch for power rankings + team_stats
- `Team.h2h_vs(other) → TeamRecord` — head-to-head
- `Team.roster_by_role()`, `.bat_leaders()`, `.pitch_leaders()`, `.errors_committed()`
- `Player.get_with_team(id)`, `.batting_line()`, `.pitching_line()`, `.batting_log()`, `.pitching_log()`, `.batting_sparkline()`, `.pitching_sparkline()`, `.draft_info()`, `.attributes()`
- `Player.all_with_attrs_and_overall()` — the `/jugadores` listing with computed OVR
- `Week(n).game_range`, `.completion()`, `.top_batters()`, `.top_pitchers()`; `Week.latest_with_games()`
- `Game.get(id)`, `.batting_lines()`, `.pitching_lines()`, `.is_mercy_rule`
- `models.game.recent_games(limit)` / `week_games(week_num)` — pre-joined game rows with pitcher W-L-SV tallies (consolidates the correlated-subquery pattern)

`services/standings.py::get_standings()` is the canonical standings computation (tiebreakers live there, not on `Team`). All blueprints that need "records with GB column" call it.

## Database Schema

| Table | Key columns / gotchas |
|-------|----------------------|
| `teams` | `short_name` (not `short`), `owner`, `color_primary`, `logo_file` |
| `players` | `name` (F. LastName format), `bats_throws` (not separate), `role` (lineup/bench/rotation/bullpen) |
| `schedule` | `game_num` (not `game_number`), `week_num`, `phase` |
| `games` | score, hits, errors, W/L/S pitcher IDs, `home_linescore`/`away_linescore` |
| `batting_stats` | Per-game: AB, R, H, doubles, triples, HR, RBI, BB, SO, SB |
| `pitching_stats` | `IP_outs` (total outs, use `format_ip()`), H, R, ER, BB, SO, HR_allowed, W, L, SV, pitches |
| `player_attributes` | power, contact, speed, pitch ratings (fastball thru curveball_dirt) |
| `analysts` | 3 personalities: Panfilo(1), Chequera(2), Facundo(3). Each has `equipo_favorito_id`, `equipo_odia_id` |
| `analyst_tweets` | **Two types**: game tweets (`game_id` set) shown on antesala, weekly analyses (`game_id IS NULL`) shown on weekly. Both have `week_num`. Has `likes` column |
| `tweet_commenters` | 10 fan personas for tweet replies |
| `tweet_replies` | Replies to analyst_tweets, with `commenter_id` and `likes` |
| `analyst_predictions` | Pre-season predictions (5 per analyst) |
| `analyst_game_picks` | Per-game winner predictions. UNIQUE(analyst_id, schedule_id) |
| `weekly_awards` | POTW, power_rankings (JSON), `game_of_week_id` per week |
| `draft_picks` | `pick_num`, `round`, `team_id`, `player_id`, `position_drafted` |
| `newspaper_editions` | `edition_num` (1-6), `articles` (JSON array), `interview` (JSON), `headline` |

## Game Data Entry — Complete Workflow

**For each game, do ALL of these steps in order:**

### Step 1: Parse box score screenshots

Games folder: `Games/game{N}/` with 6 PNG screenshots + `lanzamientos.txt`.

| Screenshot | Content |
|---|---|
| 1 | Away batting (top half) + linescore |
| 2 | Away batting (remaining + totals + extras: 2B, 3B, HR, IMP, SB, E) |
| 3 | Home batting (top half) |
| 4 | Home batting (remaining + totals + extras) |
| 5 | Away pitching |
| 6 | Home pitching |

**MANDATORY: Preprocess all screenshots BEFORE reading.** The raw 1280x720 Game Bar captures use pixel-art bitmap fonts that Claude's vision model consistently misreads at native resolution — 0/1, 2/3, 4/6 confusions are routine and will corrupt the data.

**Default — `game-screenshot-ocr` skill** (nearest-neighbor upscale + adaptive Gaussian threshold):
```bash
python C:/Users/ernes/.claude/skills/game-screenshot-ocr/scripts/preprocess.py \
  --batch "Games/gameN/"
```
Output: `Games/gameN/enhanced/` with `_hc.png` suffix. Best for pixel-art bitmap fonts — preserves sharp pixel boundaries.

**Fallback — `computer-vision-opencv` pipeline** (CLAHE + Lanczos + Otsu threshold):
```bash
python scripts/preprocess_cv2.py --batch "Games/gameN/"
```
Output: `Games/gameN/enhanced_cv2/` with `_cv2.png` suffix. Use when the default produces ambiguous results on a specific screenshot — the different preprocessing approach (bilateral filtering, global threshold) may resolve digits the adaptive threshold struggles with.

**Disambiguation workflow** (proven across 28-game / 6,000+ data point audit):
1. **Skill 1 is primary.** Read all enhanced `_hc.png` images.
2. **If a value is ambiguous**, run Skill 2 on that specific screenshot and re-read. The different preprocessing (bilateral filter, global threshold) often resolves digits Skill 1 struggles with.
3. **If both pipelines disagree or are unclear**, ask the user.

Read the enhanced images, not the originals.

**Parsing order:** Screenshots 2 & 4 first (totals), then 5 & 6 (pitching), then 1 & 3 (individual batting).

**Column mappings:** VB=AB, C=R, H=H, IMP=RBI, BB=BB, SO=SO, AVE=verification only. Pitching: INN=IP_outs, C=R, CL=ER, PCL=skip.

**Validation (mandatory cross-checks before insert):**
- **AVE column**: `H / AB` must equal the displayed AVE. If it doesn't, you misread H or AB. This is the strongest single-field check.
- **Pitching vs opposing batting totals**: pitcher H/BB/SO/HR sums must match the *opposing* team's batting totals. Critical: away pitching HR_allowed must match **home** batting HR (not away batting HR) — getting the team direction wrong was the #1 cross-check mistake in the audit.
- **Team totals**: individual stat rows must sum to the displayed team total row.
- **Linescore R**: must match team R total.

**`lanzamientos.txt` is REQUIRED, not informational.** It lists each pitcher and their pitch count (e.g. `Vega 49`). These map directly to `pitching_stats.pitches` and drive the unavailable-pitchers rest logic on the schedule page. Every pitcher in the box score must have their `pitches` value passed to `insert_game()` — never leave it at 0. If a pitcher appears in the box score but not in lanzamientos (very low pitch count reliever), use 0 only after confirming they're absent from the file.

### Step 2: Insert game data

**Must run inside Flask app context** — `insert_game()` uses `get_db()` which requires it:

```python
from app import create_app
from services.game_import import insert_game

app = create_app()
with app.app_context():
    game_id = insert_game(
        schedule_id=N,
        home_runs=X, away_runs=Y,
        home_hits=X, away_hits=Y,
        home_errors=X, away_errors=Y,
        home_linescore='R,R,R,R,R,R,R,R,R',      # away: all digits
        away_linescore='R,R,R,R,R,R,R,R,R',       # home winner: last entry is 'X'
        wp=('F. Last', 'TEAM'),                    # (name, short_name) tuples
        lp=('F. Last', 'TEAM'),
        sv=('F. Last', 'TEAM'),                    # or None
        batting=[
            {'name':'F. Last','team':'TEAM','AB':4,'R':0,'H':1,'RBI':0,
             'BB':0,'SO':1,'2B':0,'3B':0,'HR':0,'SB':0},
            # ... all batters, away team first then home team
        ],
        pitching=[
            {'name':'F. Last','team':'TEAM','IP':'6.0','H':5,'R':2,'ER':2,
             'BB':1,'SO':4,'HR':1,'W':1,'L':0,'SV':0,'pitches':85},
            # ... all pitchers, away team first then home team
        ],
    )
```

`insert_game()` validates via 7 cross-checks and **raises ValueError** on failure.

**Mercy-rule games (< 9 innings):** the IP-count check expects ≥24 outs (away) / ≥27 outs (home). A mercy-rule game will trip this even though the data is valid. The `ValueError` is raised **after** the DB commit, so the game is already saved — catch the exception if the only failures are `"only N outs, expected >= M"` and continue. **Do not `print(msg)` raw on Windows** — the failure message contains `✗` (U+2717) and the default `cp1252` stdout encoding will crash with `UnicodeEncodeError`. Either strip it, encode with `errors='replace'`, or run with `PYTHONIOENCODING=utf-8`.

### Step 3: Generate post-game tweets (MANDATORY)

**Every game needs 3 analyst tweets + fan replies.** Use `save_game_tweets()`.

**Analysts:**
| ID | Handle | Style | Fav | Hate |
|----|--------|-------|-----|------|
| 1 | Panfilo | Nostalgic, suffering, pitcher-focused | PRI | IND |
| 2 | Chequera | ALL CAPS, exaggerated, power-obsessed | GRA | CAV |
| 3 | Facundo | Formal, disciplined, methodical | SCU | LTU |

**10 Fan commenters for replies:**
| ID | Handle | Style |
|----|--------|-------|
| 1 | ElPelotero85 | Casual fan, Cuban slang |
| 2 | YasnielDLH | Stats guy, numbers, hashtags |
| 3 | LaViejaMarta | Grandma, emotional, grandson |
| 4 | TioRafael | Old school, 80s comparisons |
| 5 | MayelinPR | Pinar superfan, defensive |
| 6 | ElProfe_Beisbol | Technical, corrects everyone |
| 7 | NegroDeLoma | Santiago fan, loud, rivalry |
| 8 | Carlitosss | Teen, basic questions |
| 9 | DonaMercedes | Gossip, barrio news |
| 10 | ElGuajiro_VCL | Villa Clara farmer, proverbs |

**Tweet rules:** 1 sentence + 1 hashtag per analyst. 1-3 replies per tweet from random fans. Likes auto-randomized.

```python
from services.weekly import save_game_tweets
save_game_tweets(game_id=N, tweets=[
    {"analyst_id": 1, "texto": "Panfilo reaction. #Hashtag",
     "replies": [{"commenter_id": 3, "texto": "LaViejaMarta reply"}]},
    {"analyst_id": 2, "texto": "CHEQUERA CAPS REACTION! #Hashtag",
     "replies": [{"commenter_id": 1, "texto": "ElPelotero85 reply"}]},
    {"analyst_id": 3, "texto": "Facundo formal analysis. #Hashtag",
     "replies": [{"commenter_id": 6, "texto": "ElProfe reply"}]},
])
```

## Helper Scripts

- `python scripts/query.py "<SQL>"` — ad-hoc SQL runner against `torneo.db` with `sqlite3.Row` + pretty-print. Replacement for the missing `sqlite3` CLI on this machine. Flags: `--tables`, `--schema <table>`, `--limit N`. Reach for this instead of `python -c "import sqlite3; ..."` one-liners.
- `python scripts/finalize_week.py N` — **use after all 4 games of week N are boxscored.** Runs `auto_generate_week(N+1)` (persists N rankings + N+1 picks + N+1 GotW), then prints POTW candidates, the rankings skeleton with `<-- BLANK` flags on every missing blurb, and paste-ready `save_weekly_awards` / `save_weekly_tweets` templates. Idempotent — re-running preserves any blurbs you've already saved (`auto_generate_week` merges blurbs by `team_id`).
- `python scripts/preprocess_cv2.py --batch "Games/gameN/"` — fallback image preprocessor (see Game Data Entry Step 1).

## Weekly Content Workflow

After all 4 games of week N are entered:

### Step 1: Generate weekly report
Run `python weekly.py N` — prints results, standings, top performers, upcoming games with rankings.
(Or jump straight to `python scripts/finalize_week.py N` which auto-runs the deterministic pieces first.)

### Step 2: Save weekly content
- **POTW + Power Rankings**: `compute_power_rankings(N)` then `save_weekly_awards(N, potw_id, summary, rankings, game_of_week_id)`
- **Per-team blurbs on the rankings are MANDATORY.** `compute_power_rankings()` does NOT generate them — each entry comes back with `blurb` absent or empty. Write a 1–2 sentence `blurb` per team (who starred, who collapsed, what the takeaway is) and inject it into each dict before saving. `/weekly` and the power-rankings panel read this field; missing blurbs render as empty space.
- **Weekly analyses** (3 per week, 4 sentences each, NOT tweets): `save_weekly_tweets(N, [...])`
  - These are longer analysis pieces shown on `/weekly`, different from per-game tweets
  - `save_weekly_tweets` only deletes weekly tweets (`game_id IS NULL`), not game tweets

### Step 3: Generate predictions for week N+1
```python
from services.weekly import generate_game_picks, save_game_picks, save_game_of_week
picks = generate_game_picks(N+1)  # weighted: fav bias > rankings > pitching > H2H
save_game_picks(N+1, picks)
save_game_of_week(N+1)  # computes + persists, returns schedule_id
```

Predictions show on `/schedule` — analyst avatars next to predicted winner, gold "Juego de la Semana" badge reads from `weekly_awards.game_of_week_id`. All weekly services live in `services/weekly.py` — there is no `blueprints/weekly/services.py`.

### Analyst prediction weights
| Factor | Panfilo | Chequera | Facundo |
|--------|---------|----------|---------|
| Favorite/hate bias | 0.40 | 0.45 | 0.35 |
| Power rankings | 0.20 | 0.25 | 0.25 |
| Pitcher matchup | 0.25 | 0.15 | 0.25 |
| Head-to-head | 0.15 | 0.15 | 0.15 |

Prediction accuracy tracked via `get_prediction_records()` — correct/total/pct per analyst.

## Newspaper — "En Tres y Dos"

Fictional Cuban baseball newspaper published every 4 weeks (6 editions total, at weeks 4/8/12/16/20/24). Lives at `/periodico` with its own cream-paper serif aesthetic.

### Edition content sections:
| Section | Description |
|---------|-------------|
| Portada | Masthead, headline, subheadline |
| El Panorama | Standings + power rankings editorial |
| La Nota del Dia | Feature article on the biggest 4-week story |
| Radar Estadistico | 3-4 hidden stat anomalies with callout boxes |
| La Carrera | Award race deep-dive (Kindelan + Lazo) |
| Entrevista | Analyst-hosted player interview (rotating: Ed.1=Panfilo, Ed.2=Chequera, Ed.3=Facundo, repeat) |
| Retrovisores | Narrative callbacks to past tweets/predictions that aged well or badly |

### Data model
`newspaper_editions` table with `articles` (JSON array) and `interview` (JSON object). Services at `blueprints/periodico/services.py`: `save_edition()`, `get_edition()`, `get_all_editions()`.

### Article JSON shape
```json
{"type": "feature|stats|column|callback|sidebar", "title": "...", "subtitle": "...", "body": "<p>HTML body</p>", "author": null, "stat_callout": {"value": "23", "label": "hits in one game"}}
```

### Interview JSON shape
```json
{"analyst_id": 1, "player_id": 42, "title": "Entrevista a J. Pedroso", "questions": [{"q": "Question text", "a": "Answer text"}]}
```

### Generation workflow
Editions are handcrafted content, not auto-generated. After 4 weeks of games:
```python
from blueprints.periodico.services import save_edition
save_edition(edition_num=1, week_num=4, headline="...", subheadline="...", articles=[...], interview={...})
```

## Player Attributes — Entry & Audit

### Field mapping

**Batter:** vs ZUR (Pod/Con) → `power_vs_l` / `contact_vs_l`. vs DER → `power_vs_r` / `contact_vs_r`. Vel → `speed`.

**Pitcher:** ESTAMINA → `stamina`, plus an arsenal of ≤6 pitch ratings:

| R4C | SLD | CRV | SNK | TND | SPL | SCR | CBB | RCT | CCL |
|---|---|---|---|---|---|---|---|---|---|
| fastball | slider | curveball | sinker | changeup | splitter | screwball | curveball_dirt | cutter | circle_changeup |

`CBB` ("dirty curve") is distinct from `CRV`. `CCL` (circle change) is rare — only G. Concepcion (IND) has it across all 8 teams.

### Player photos

All 8 teams complete (200 photos, audited). Path: `static/graphics/players/<SHORT>/<Slug>.png`. Slug: strip periods, join with underscores (`R. Lunar` → `R_Lunar.png`). Duplicate names append jersey number (`Y_Perez_11.png` vs `Y_Perez_56.png`).

### Audit status

All 8 teams' attributes and `full_name` values have been audited and corrected. Audit scripts (`crop_for_audit.py`, `audit_attributes.py`, `fix_team_attributes.py`) remain in `scripts/` for future use. For fresh attribute entry, use `services/attributes_import.py :: bulk_upsert()`. For duplicate names within a team, use `upsert_attributes(player_id, attrs)` directly.
