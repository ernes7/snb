# MVP Cuba 2011 Tournament Tracker

Baseball tournament tracker for a simulated Cuban National Series season played in MVP Baseball 2005. Two owners (Ernesto and Junior) each control 4 teams. Tracks standings, schedules, game results, player stats, draft, playoffs, antesala (pre-game show), and weekly recaps.

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
- Fat models / thin views — routes are glue, logic in services
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
│   ├── weekly/                   # /weekly, /weekly/<week_num>
│   └── periodico/                # /periodico (newspaper "En Tres y Dos")
├── services/
│   ├── standings.py              # get_standings(), get_all_teams()
│   ├── player_stats.py           # get_all_batting_lines(), get_all_pitching_lines() — shared aggregates
│   ├── weekly.py                 # weekly summaries, tweets, predictions, game picks
│   ├── power_rankings.py         # compute_power_rankings()
│   ├── game_import.py            # insert_game() + validate_game()
│   └── attributes_import.py      # bulk_upsert()
├── lib/
│   ├── utils.py                  # format_ip() — Jinja2 global
│   └── stats.py                  # BattingLine, PitchingLine — rate stat source of truth
├── templates/
│   ├── base.html                 # Layout: sidebar, {% block content %}, {% block scripts %}
│   ├── components/               # Reusable macros (see UI Components below)
│   ├── errors/                   # 404.html, 500.html
│   └── *.html                    # Page templates
├── static/
│   ├── style.css                 # Design system (see DESIGN.md)
│   ├── app.js                    # Sidebar toggle, card animations, initSortableTable()
│   └── graphics/                 # Team logos, player photos, analyst avatars, banners
├── schema.sql                    # Reference DDL only — do NOT run on populated DB
├── weekly.py                     # CLI: python weekly.py <week_num>
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
| `newspaper_editions` | `edition_num` (1-6), `articles` (JSON array), `interview` (JSON), `headline` |

## Domain Rules

- **8 teams**: Ernesto (GRA, SSP, PRI, LTU) / Junior (SCU, VCL, IND, CAV)
- **Regular season:** 96 games (4 per week, 24 weeks), each team plays 24
- **Standings tiebreakers** (`services/standings.py`): sort order is win% → in-group tiebreaker → overall run differential. A **2-way tie** uses head-to-head wins, then run differential *within those same H2H games* if H2H is level — **unless the two teams share an owner** (same-owner teams never play each other in this league), in which case the tiebreaker is overall run differential directly. A **3+ way tie** uses run differential restricted to games played among the tied teams only. If the in-group tiebreaker also ties, the sort falls through to overall run differential. The GB column is computed from the top team's W-L after sorting — two teams at the top show "-" even if they got there by tiebreak.
- **Playoffs:** Top 4 advance. Best-of-5 semis and finals
- **Draft:** 3 rounds, 8 picks each. Players marked `is_drafted=1`
- **Season awards:** **Premio Kindelan** (batter MVP, OPS-driven) and **Premio Lazo** (pitcher Cy Young, ERA-driven). Full scoring formula in `memory/project_mvp_awards.md` and `blueprints/mvp_race/services.py`. Live race rendered at `/mvp-race`. Team multiplier is 2% steps (1.06 to 0.92). Batter triple crown = AVG/HR/RBI. Pitcher triple crown = SO/ERA/W (not IP — IP correlates too much with other stats). Tiebreakers in bonus grading: most AB for batters, most IP_outs for pitchers.
- **Leader tiebreakers**: When stats tie on `/leaders`, batters break ties by most AB, pitchers by most IP_outs. Same logic used in MVP race bonus grading (`_grade_ranks` in `blueprints/mvp_race/services.py`).
- **Newspaper "En Tres y Dos"**: `/periodico` route, 6 editions (every 4 weeks). See dedicated section below.

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

**Parsing order:** Screenshots 2 & 4 first (totals), then 5 & 6 (pitching), then 1 & 3 (individual batting).

**Column mappings:** VB=AB, C=R, H=H, IMP=RBI, BB=BB, SO=SO, AVE=verification only. Pitching: INN=IP_outs, C=R, CL=ER, PCL=skip.

**`lanzamientos.txt` is REQUIRED, not informational.** It lists each pitcher and their pitch count (e.g. `Vega 49`). These map directly to `pitching_stats.pitches` and drive the unavailable-pitchers rest logic on the schedule page. Every pitcher in the box score must have their `pitches` value passed to `insert_game()` — never leave it at 0. If a pitcher appears in the box score but not in lanzamientos (very low pitch count reliever), use 0 only after confirming they're absent from the file.

### Step 2: Insert game data

```python
from services.game_import import insert_game
game_id = insert_game(schedule_id=N, home_runs=X, away_runs=Y, ...)
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

## Weekly Content Workflow

After all 4 games of week N are entered:

### Step 1: Generate weekly report
Run `python weekly.py N` — prints results, standings, top performers, upcoming games with rankings.

### Step 2: Save weekly content
- **POTW + Power Rankings**: `compute_power_rankings(N)` then `save_weekly_awards(N, potw_id, summary, rankings, game_of_week_id)`
- **Per-team blurbs on the rankings are MANDATORY.** `compute_power_rankings()` does NOT generate them — each entry comes back with `blurb` absent or empty. Write a 1–2 sentence `blurb` per team (who starred, who collapsed, what the takeaway is) and inject it into each dict before saving. `/weekly` and the power-rankings panel read this field; missing blurbs render as empty space.
- **Weekly analyses** (3 per week, 4 sentences each, NOT tweets): `save_weekly_tweets(N, [...])`
  - These are longer analysis pieces shown on `/weekly`, different from per-game tweets
  - `save_weekly_tweets` only deletes weekly tweets (`game_id IS NULL`), not game tweets

### Step 3: Generate predictions for week N+1
```python
from services.weekly import generate_game_picks, save_game_picks, pick_game_of_week
picks = generate_game_picks(N+1)  # weighted: fav bias > rankings > pitching > H2H
save_game_picks(N+1, picks)
gotw_sched_id = pick_game_of_week(N+1)  # closest power ranking matchup

# pick_game_of_week() only COMPUTES — you must persist it yourself.
# For past weeks save_weekly_awards(N, ...) does this. For N+1 there's no
# POTW/rankings yet, so upsert weekly_awards directly with just the GotW:
from db import get_db
get_db().execute("""
    INSERT INTO weekly_awards (week_num, game_of_week_id) VALUES (?, ?)
    ON CONFLICT(week_num) DO UPDATE SET game_of_week_id = excluded.game_of_week_id
""", (N+1, gotw_sched_id))
get_db().commit()
```

Predictions show on `/schedule` — analyst avatars next to predicted winner, gold "Juego de la Semana" badge reads from `weekly_awards.game_of_week_id`. If the badge doesn't render for the upcoming week, the upsert above is what's missing. All weekly services live in `services/weekly.py` — there is no `blueprints/weekly/services.py`.

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

### Player photo organization

Photos live at `static/graphics/players/<SHORT>/<NormalizedName>.png`. Slug rules: strip periods, join with underscores. `R. Lunar` → `R_Lunar.png`, `C. Barrabi Jr.` → `C_Barrabi_Jr.png`. Duplicates within a team append the jersey number: `Y_Perez_11.png` (bench) vs `Y_Perez_56.png` (rotation).

**Status:** All 8 teams complete (200 photos, all audited and corrected).

### Workflow A: New screenshots → organized

1. Capture roster screens → `C:\Users\ernes\Videos\Captures\`.
2. `python scripts/crop_attributes.py` — crops the top 43% of each PNG to `Videos/Captures/cropped/`.
3. Identify each cropped image (read team + player name off the screen, match to DB) and append to `.scratch/roster_ids.md`:
   ```
   <timestamp> | <TEAM> | <db_name> | <screen_label_for_reference>
   10_24_18 AM | VCL | R. Lunar | RF Ramon E Lunar #66
   ```
4. `python scripts/organize_roster_pics.py` — moves each image into `static/graphics/players/<TEAM>/<slug>.png`. Idempotent.

### Workflow B: Audit existing photos against DB

When a team's `player_attributes` rows are suspect (typos, swapped columns, wrong-row entries):

1. `python scripts/crop_for_audit.py` — generates 3× upscaled crops at `.scratch/attr_crops/<TEAM>/`. **`CROP_BOX` right edge must be ≥0.85** — at 0.82 the second pitch column is silently clipped (this is how J. Martinez's `SNK=95` got missed on the first pass).
2. View each crop and append to `.scratch/attr_audit.md` in the strict format the parser expects:
   ```
   ## VCL batters
   VCL/R_Lunar.png | 90 90 | 80 90 | 90
                     pvl cvl  pvr cvr  spd

   ## VCL pitchers
   VCL/J_Martinez.png | 96 | R4C=97 SLD=95 SNK=95 SPL=93 CRV=93
                        stm   <pitch>=<value> pairs in any order/subset
   ```
   The `## TEAM batters` / `## TEAM pitchers` headers are mandatory — pitcher lines only parse under a `pitcher` section. Parser is `BATTER_LINE` / `PITCHER_LINE` / `parse_pitch_rest` in `scripts/audit_attributes.py`.
3. `python scripts/audit_attributes.py` — diffs every line against `player_attributes` and reports `DB=X SCREEN=Y` mismatches. A `"DB=X but NOT on screen"` line means the original entry mapped a value to the wrong pitch column.
4. `python scripts/fix_team_attributes.py <TEAM>` (dry run) → `python scripts/fix_team_attributes.py <TEAM> --apply`. Pitch columns absent from the audit line are **reset to NULL** — the on-screen view is authoritative for pitch arsenal.

### Step 5: Verify `players.full_name` (MANDATORY)

The `players` table has both `name` (abbreviated, e.g. "U. Bermudez") and `full_name` (e.g. "Ubisney Bermudez"). **Always verify `full_name` against the on-screen text** during audit — the initial data entry got 45 out of 158 full names wrong (wrong first names like "Ulises" instead of "Ubisney", "Osmani" instead of "Oscar", etc.). Also fill in any NULL `full_name` values for bench/bullpen players added later. The screenshot header shows the full name clearly — read it and UPDATE the DB.

### Audit gotchas (from the full 8-team audit)

- **Always verify `full_name` from the screenshot header.** Initial entry had ~28% error rate on full names — wrong first names, missing middle initials, NULL values on bench/bullpen players.
- **Trust `players.role` over the on-screen position label.** The game sometimes labels a rotation pitcher as "RP" or vice versa; the DB role is what drives lineup/rotation logic.
- **`unslugify` strips trailing periods** (`C_Barrabi_Jr` → `C. Barrabi Jr`). Both fix and audit scripts try `name` and `name + "."` when looking up `players.name`.
- **Common error patterns observed in entered data:**
  - Swapped `contact_vs_l` ↔ `contact_vs_r` (A. Pestano style)
  - Pitch columns shuffled — fastball/curveball/changeup rotated (Y. Perez #56 style)
  - Single-field 15–25 point gaps from wrong-row entries (A. Zamora PvL, L. Borroto stamina)
  - Pitch on screen but missing from DB entirely (Y. Lopez `curveball_dirt`)
  - Lots of 1–3 point typos throughout
- **Save round-trip cost** — when reading 25+ images, batch them in single-message parallel `Read` calls and only update `attr_audit.md` once per batch. Don't re-crop unless the right-edge bound is wrong.

### Bulk entry (`services/attributes_import.py :: bulk_upsert()`)

Still the right tool for fresh entry of an unaudited team. For duplicate names within a team, pass `upsert_attributes(player_id, attrs)` with the specific player ID instead.
